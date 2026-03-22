import os
from datetime import datetime

from fastapi import APIRouter, Body, File, Form, Query, UploadFile
from tortoise.expressions import Q

from app.controllers.message import call_controller, message_controller
from app.core.ctx import CTX_USER_ID
from app.models.admin import CallRecord, MessageReadStatus, MessageRecord, User
from app.models.enums import CallStatus
from app.schemas.base import Success, SuccessExtra
from app.schemas.messages import CallCreate, MessageCreate
from app.settings.config import settings

router = APIRouter()


@router.post("/send", summary="发送消息")
async def send_message(msg_in: MessageCreate):
    user_id = CTX_USER_ID.get()
    msg = await message_controller.send_message(sender_id=user_id, obj_in=msg_in)
    return Success(msg="发送成功", data=await msg.to_dict())


@router.get("/list", summary="获取消息列表（全量）")
async def list_all_messages(
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    ticket_id: int = Query(None, description="工单ID"),
    msg_type: str = Query("", description="消息类型"),
    sender_id: int = Query(None, description="发送人ID"),
):
    q = Q()
    if ticket_id is not None:
        q &= Q(ticket_id=ticket_id)
    if msg_type:
        q &= Q(msg_type=msg_type)
    if sender_id is not None:
        q &= Q(sender_id=sender_id)

    user_id = CTX_USER_ID.get()
    total = await MessageRecord.filter(q).count()
    objs = await MessageRecord.filter(q).offset((page - 1) * page_size).limit(page_size).order_by("-created_at")
    # Get read status for current user
    msg_ids = [msg.id for msg in objs]
    read_ids = set()
    if msg_ids:
        read_records = await MessageReadStatus.filter(message_id__in=msg_ids, user_id=user_id)
        read_ids = {r.message_id for r in read_records}
    data = []
    for msg in objs:
        d = await msg.to_dict()
        d["is_read"] = msg.id in read_ids or msg.sender_id == user_id  # own messages are always "read"
        sender = await User.filter(id=msg.sender_id).first()
        d["sender_name"] = sender.alias or sender.username if sender else ""
        if msg.receiver_id:
            receiver = await User.filter(id=msg.receiver_id).first()
            d["receiver_name"] = receiver.alias or receiver.username if receiver else ""
        else:
            d["receiver_name"] = ""
        data.append(d)
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/ticket_messages", summary="获取工单消息记录")
async def get_ticket_messages(
    ticket_id: int = Query(..., description="工单ID"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(50, description="每页数量"),
):
    user_id = CTX_USER_ID.get()
    objs = await MessageRecord.filter(ticket_id=ticket_id).order_by("created_at")
    total = len(objs)

    # Per-user read status
    msg_ids = [m.id for m in objs]
    read_ids = set()
    if msg_ids:
        read_records = await MessageReadStatus.filter(message_id__in=msg_ids, user_id=user_id)
        read_ids = {r.message_id for r in read_records}

    start = (page - 1) * page_size
    end = start + page_size
    data = []
    for msg in objs[start:end]:
        d = await msg.to_dict()
        d["is_read"] = msg.id in read_ids or msg.sender_id == user_id
        d["is_mine"] = msg.sender_id == user_id
        sender = await User.filter(id=msg.sender_id).first()
        d["sender_name"] = sender.alias or sender.username if sender else ""
        if msg.receiver_id:
            receiver = await User.filter(id=msg.receiver_id).first()
            d["receiver_name"] = receiver.alias or receiver.username if receiver else ""
        else:
            d["receiver_name"] = ""
        data.append(d)

    # Auto mark all received messages as read
    unread_msg_ids = [m.id for m in objs if m.id not in read_ids and m.sender_id != user_id]
    for mid in unread_msg_ids:
        exists = await MessageReadStatus.filter(message_id=mid, user_id=user_id).exists()
        if not exists:
            await MessageReadStatus.create(message_id=mid, user_id=user_id)

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/mark_read", summary="标记消息已读")
async def mark_messages_read(message_ids: list[int] = Body(..., description="消息ID列表")):
    user_id = CTX_USER_ID.get()
    for mid in message_ids:
        exists = await MessageReadStatus.filter(message_id=mid, user_id=user_id).exists()
        if not exists:
            await MessageReadStatus.create(message_id=mid, user_id=user_id)
    return Success(msg="标记成功")


@router.get("/unread_count", summary="获取未读消息数")
async def get_unread_count():
    user_id = CTX_USER_ID.get()
    # Messages where I'm the receiver (or receiver is null = broadcast) and I haven't read
    my_messages = await MessageRecord.filter(
        Q(receiver_id=user_id) | Q(receiver_id__isnull=True)
    ).exclude(sender_id=user_id)
    msg_ids = [m.id for m in my_messages]
    if not msg_ids:
        return Success(data={"count": 0})
    read_count = await MessageReadStatus.filter(message_id__in=msg_ids, user_id=user_id).count()
    unread = len(msg_ids) - read_count
    return Success(data={"count": max(0, unread)})


@router.post("/delete", summary="删除消息")
async def delete_message(message_id: int = Body(..., embed=True, description="消息ID")):
    user_id = CTX_USER_ID.get()
    msg = await MessageRecord.filter(id=message_id).first()
    if not msg:
        return Success(msg="消息不存在", code=404)
    # Check permission: sender can delete own, superuser can delete any
    user = await User.filter(id=user_id).first()
    if msg.sender_id != user_id and not (user and user.is_superuser):
        return Success(msg="无权删除此消息", code=403)
    await msg.delete()
    # Also delete read statuses
    await MessageReadStatus.filter(message_id=message_id).delete()
    return Success(msg="删除成功")


@router.post("/upload_voice", summary="上传语音消息")
async def upload_voice_message(
    file: UploadFile = File(...),
    ticket_id: str = Form(""),
    receiver_id: str = Form(""),
    voice_duration: str = Form("0"),
):
    user_id = CTX_USER_ID.get()
    tid = int(ticket_id) if ticket_id else 0
    rid = int(receiver_id) if receiver_id else None
    dur = int(voice_duration) if voice_duration and voice_duration != "0" else None

    upload_dir = os.path.join(settings.UPLOAD_DIR, "voice_messages")
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1] if file.filename else ".mp3"
    filename = f"vmsg_{tid}_{os.urandom(4).hex()}{ext}"
    filepath = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    file_url = f"/uploads/voice_messages/{filename}"

    msg_in = MessageCreate(
        ticket_id=tid, receiver_id=rid, msg_type="voice", file_url=file_url,
        voice_duration=dur,
    )
    msg = await message_controller.send_message(sender_id=user_id, obj_in=msg_in)
    return Success(msg="上传成功", data=await msg.to_dict())


@router.post("/upload_image", summary="上传图片消息")
async def upload_image_message(
    file: UploadFile = File(...),
    ticket_id: str = Form(""),
    receiver_id: str = Form(""),
):
    user_id = CTX_USER_ID.get()
    tid = int(ticket_id) if ticket_id else 0
    rid = int(receiver_id) if receiver_id else None
    upload_dir = os.path.join(settings.UPLOAD_DIR, "images")
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"img_{tid}_{os.urandom(4).hex()}{ext}"
    filepath = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    file_url = f"/uploads/images/{filename}"

    msg_in = MessageCreate(
        ticket_id=tid, receiver_id=rid, msg_type="image", file_url=file_url,
    )
    msg = await message_controller.send_message(sender_id=user_id, obj_in=msg_in)
    return Success(msg="上传成功", data=await msg.to_dict())


@router.post("/push", summary="推送消息给指定用户")
async def push_notification(
    user_id: int = Body(..., description="目标用户ID"),
    ticket_id: int = Body(None, description="关联工单ID"),
    content: str = Body(..., description="通知内容"),
    title: str = Body("系统通知", description="通知标题"),
):
    sender_id = CTX_USER_ID.get()
    msg_in = MessageCreate(
        ticket_id=ticket_id or 0, receiver_id=user_id, msg_type="system",
        content=f"[{title}] {content}",
    )
    msg = await message_controller.send_message(sender_id=sender_id, obj_in=msg_in)
    return Success(msg="推送成功", data=await msg.to_dict())


@router.get("/my_notifications", summary="获取我的通知")
async def get_my_notifications(
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    unread_only: bool = Query(False, description="仅未读"),
):
    user_id = CTX_USER_ID.get()
    q = Q(receiver_id=user_id)
    if unread_only:
        q &= Q(is_read=False)
    total = await MessageRecord.filter(q).count()
    objs = await MessageRecord.filter(q).offset((page - 1) * page_size).limit(page_size).order_by("-created_at")
    data = []
    for msg in objs:
        d = await msg.to_dict()
        sender = await User.filter(id=msg.sender_id).first()
        d["sender_name"] = sender.alias or sender.username if sender else "系统"
        data.append(d)
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


# === WebRTC Call ===

@router.post("/call/initiate", summary="发起语音通话")
async def initiate_call(call_in: CallCreate):
    user_id = CTX_USER_ID.get()
    call = await call_controller.initiate_call(caller_id=user_id, obj_in=call_in)
    return Success(msg="通话发起成功", data=await call.to_dict())


@router.post("/call/answer", summary="接听通话")
async def answer_call(call_id: int = Body(..., embed=True)):
    call = await call_controller.update_call_status(
        call_id, CallStatus.CONNECTED, start_time=datetime.now()
    )
    return Success(msg="已接听", data=await call.to_dict())


@router.post("/call/hangup", summary="挂断通话")
async def hangup_call(call_id: int = Body(..., embed=True)):
    call = await call_controller.get(id=call_id)
    duration = 0
    if call.start_time:
        duration = int((datetime.now() - call.start_time).total_seconds())
    call = await call_controller.update_call_status(
        call_id, CallStatus.ENDED, end_time=datetime.now(), duration=duration
    )
    return Success(msg="已挂断", data=await call.to_dict())


@router.get("/call/records", summary="查询通话记录")
async def get_call_records(
    ticket_id: int = Query(None, description="工单ID"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
):
    q = Q()
    if ticket_id:
        q &= Q(ticket_id=ticket_id)
    total, objs = await call_controller.list(
        page=page, page_size=page_size, search=q, order=["-created_at"]
    )
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)
