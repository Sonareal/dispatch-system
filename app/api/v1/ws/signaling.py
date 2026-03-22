"""
WebSocket Signaling Server for Voice Calls

Protocol:
  Client connects to: ws://host/api/v1/ws/signaling?token=JWT_TOKEN

  Messages (JSON):
    Client → Server:
      { "type": "call_initiate", "ticket_id": 1, "callee_id": 2 }
      { "type": "call_answer", "call_id": 1 }
      { "type": "call_reject", "call_id": 1 }
      { "type": "call_hangup", "call_id": 1 }
      { "type": "call_candidate", "call_id": 1, "candidate": {...} }  // ICE candidate
      { "type": "call_offer", "call_id": 1, "sdp": "..." }           // SDP offer
      { "type": "call_answer_sdp", "call_id": 1, "sdp": "..." }      // SDP answer
      { "type": "ping" }

    Server → Client:
      { "type": "incoming_call", "call_id": 1, "caller_id": 1, "caller_name": "...", "ticket_id": 1, "room_id": "..." }
      { "type": "call_accepted", "call_id": 1 }
      { "type": "call_rejected", "call_id": 1 }
      { "type": "call_ended", "call_id": 1, "duration": 30 }
      { "type": "call_candidate", "call_id": 1, "candidate": {...} }
      { "type": "call_offer", "call_id": 1, "sdp": "..." }
      { "type": "call_answer_sdp", "call_id": 1, "sdp": "..." }
      { "type": "call_failed", "call_id": 1, "reason": "..." }
      { "type": "pong" }
      { "type": "error", "msg": "..." }
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.models.admin import CallRecord, User
from app.models.enums import CallStatus
from app.utils.jwt_utils import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter()

# Connected clients: user_id -> WebSocket
connected_clients: dict[int, WebSocket] = {}
# Active calls: call_id -> CallRecord id
active_calls: dict[int, dict] = {}


async def authenticate_ws(token: str) -> Optional[int]:
    """Verify JWT token and return user_id"""
    try:
        payload = decode_access_token(token)
        return payload.get("user_id")
    except Exception:
        return None


async def send_to_user(user_id: int, data: dict):
    """Send message to a specific user if they're connected"""
    ws = connected_clients.get(user_id)
    if ws:
        try:
            await ws.send_json(data)
            return True
        except Exception:
            connected_clients.pop(user_id, None)
            return False
    return False


@router.websocket("/signaling")
async def websocket_signaling(websocket: WebSocket, token: str = Query(...)):
    # Authenticate
    user_id = await authenticate_ws(token)
    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()

    # Register connection
    old_ws = connected_clients.get(user_id)
    if old_ws:
        try:
            await old_ws.send_json({"type": "replaced", "msg": "Another device connected"})
            await old_ws.close(code=4002)
        except Exception:
            pass
    connected_clients[user_id] = websocket

    user = await User.filter(id=user_id).first()
    user_name = (user.alias or user.username) if user else f"User#{user_id}"
    logger.info(f"WS connected: user_id={user_id} ({user_name})")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "msg": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "call_initiate":
                await handle_call_initiate(user_id, user_name, msg, websocket)

            elif msg_type == "call_answer":
                await handle_call_answer(user_id, msg, websocket)

            elif msg_type == "call_reject":
                await handle_call_reject(user_id, msg, websocket)

            elif msg_type == "call_hangup":
                await handle_call_hangup(user_id, msg, websocket)

            elif msg_type in ("call_candidate", "call_offer", "call_answer_sdp"):
                await handle_webrtc_relay(user_id, msg, websocket)

            else:
                await websocket.send_json({"type": "error", "msg": f"Unknown type: {msg_type}"})

    except WebSocketDisconnect:
        logger.info(f"WS disconnected: user_id={user_id}")
    except Exception as e:
        logger.error(f"WS error for user_id={user_id}: {e}")
    finally:
        if connected_clients.get(user_id) == websocket:
            connected_clients.pop(user_id, None)
        # Clean up any active calls for this user
        await cleanup_user_calls(user_id)


async def handle_call_initiate(caller_id: int, caller_name: str, msg: dict, ws: WebSocket):
    """Handle call initiation"""
    ticket_id = msg.get("ticket_id")
    callee_id = msg.get("callee_id")

    if not ticket_id or not callee_id:
        await ws.send_json({"type": "error", "msg": "Missing ticket_id or callee_id"})
        return

    # Create call record
    import uuid
    room_id = f"room_{uuid.uuid4().hex[:12]}"
    call = CallRecord(
        ticket_id=ticket_id,
        caller_id=caller_id,
        callee_id=callee_id,
        status=CallStatus.RINGING,
        room_id=room_id,
    )
    await call.save()

    # Track active call
    active_calls[call.id] = {
        "caller_id": caller_id,
        "callee_id": callee_id,
        "ticket_id": ticket_id,
        "room_id": room_id,
    }

    # Notify caller: call created
    await ws.send_json({
        "type": "call_created",
        "call_id": call.id,
        "room_id": room_id,
        "callee_id": callee_id,
    })

    # Notify callee: incoming call
    callee_online = await send_to_user(callee_id, {
        "type": "incoming_call",
        "call_id": call.id,
        "caller_id": caller_id,
        "caller_name": caller_name,
        "ticket_id": ticket_id,
        "room_id": room_id,
    })

    if not callee_online:
        # Callee is offline
        call.status = CallStatus.MISSED
        await call.save()
        active_calls.pop(call.id, None)
        await ws.send_json({
            "type": "call_failed",
            "call_id": call.id,
            "reason": "对方不在线",
        })

    # Auto-timeout after 30 seconds
    asyncio.create_task(_call_timeout(call.id, 30))


async def handle_call_answer(user_id: int, msg: dict, ws: WebSocket):
    """Handle call answer"""
    call_id = msg.get("call_id")
    if not call_id:
        return

    call = await CallRecord.filter(id=call_id).first()
    if not call or call.callee_id != user_id:
        await ws.send_json({"type": "error", "msg": "Invalid call"})
        return

    if call.status != CallStatus.RINGING:
        await ws.send_json({"type": "error", "msg": "Call is not ringing"})
        return

    call.status = CallStatus.CONNECTED
    call.start_time = datetime.now()
    await call.save()

    # Notify caller
    await send_to_user(call.caller_id, {
        "type": "call_accepted",
        "call_id": call.id,
    })

    # Confirm to callee
    await ws.send_json({
        "type": "call_connected",
        "call_id": call.id,
        "room_id": call.room_id,
    })


async def handle_call_reject(user_id: int, msg: dict, ws: WebSocket):
    """Handle call rejection"""
    call_id = msg.get("call_id")
    if not call_id:
        return

    call = await CallRecord.filter(id=call_id).first()
    if not call:
        return

    call.status = CallStatus.ENDED
    call.end_time = datetime.now()
    await call.save()
    active_calls.pop(call_id, None)

    # Notify caller
    await send_to_user(call.caller_id, {
        "type": "call_rejected",
        "call_id": call.id,
    })

    # Confirm to callee
    await ws.send_json({
        "type": "call_ended",
        "call_id": call.id,
        "duration": 0,
    })


async def handle_call_hangup(user_id: int, msg: dict, ws: WebSocket):
    """Handle call hangup"""
    call_id = msg.get("call_id")
    if not call_id:
        return

    call = await CallRecord.filter(id=call_id).first()
    if not call:
        return

    duration = 0
    if call.start_time:
        duration = int((datetime.now() - call.start_time).total_seconds())

    call.status = CallStatus.ENDED
    call.end_time = datetime.now()
    call.duration = duration
    await call.save()
    active_calls.pop(call_id, None)

    # Notify the other party
    other_id = call.callee_id if user_id == call.caller_id else call.caller_id
    await send_to_user(other_id, {
        "type": "call_ended",
        "call_id": call.id,
        "duration": duration,
    })

    await ws.send_json({
        "type": "call_ended",
        "call_id": call.id,
        "duration": duration,
    })


async def handle_webrtc_relay(sender_id: int, msg: dict, ws: WebSocket):
    """Relay WebRTC signaling messages (SDP offer/answer, ICE candidates)"""
    call_id = msg.get("call_id")
    if not call_id:
        return

    call_info = active_calls.get(call_id)
    if not call_info:
        call = await CallRecord.filter(id=call_id).first()
        if not call:
            return
        call_info = {"caller_id": call.caller_id, "callee_id": call.callee_id}

    # Determine target user
    if sender_id == call_info["caller_id"]:
        target_id = call_info["callee_id"]
    elif sender_id == call_info["callee_id"]:
        target_id = call_info["caller_id"]
    else:
        return

    # Relay the message as-is
    await send_to_user(target_id, msg)


async def cleanup_user_calls(user_id: int):
    """Clean up active calls when user disconnects"""
    for call_id, info in list(active_calls.items()):
        if info["caller_id"] == user_id or info["callee_id"] == user_id:
            call = await CallRecord.filter(id=call_id).first()
            if call and call.status in (CallStatus.INITIATING, CallStatus.RINGING, CallStatus.CONNECTED):
                duration = 0
                if call.start_time:
                    duration = int((datetime.now() - call.start_time).total_seconds())
                call.status = CallStatus.ENDED
                call.end_time = datetime.now()
                call.duration = duration
                await call.save()

                # Notify other party
                other_id = info["callee_id"] if user_id == info["caller_id"] else info["caller_id"]
                await send_to_user(other_id, {
                    "type": "call_ended",
                    "call_id": call_id,
                    "duration": duration,
                    "reason": "对方已断开",
                })
            active_calls.pop(call_id, None)


async def _call_timeout(call_id: int, timeout_seconds: int):
    """Auto-timeout a ringing call"""
    await asyncio.sleep(timeout_seconds)
    call = await CallRecord.filter(id=call_id).first()
    if call and call.status == CallStatus.RINGING:
        call.status = CallStatus.MISSED
        call.end_time = datetime.now()
        await call.save()
        active_calls.pop(call_id, None)

        # Notify both parties
        await send_to_user(call.caller_id, {
            "type": "call_failed",
            "call_id": call_id,
            "reason": "对方未接听",
        })
        await send_to_user(call.callee_id, {
            "type": "call_ended",
            "call_id": call_id,
            "reason": "未接听",
        })
