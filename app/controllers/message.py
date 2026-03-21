import logging
import uuid

from tortoise.expressions import Q

from app.core.crud import CRUDBase
from app.models.admin import CallRecord, MessageRecord, User
from app.models.enums import CallStatus, MessageType
from app.schemas.messages import CallCreate, MessageCreate
from app.settings import settings
from app.utils.wechat import send_subscribe_message

logger = logging.getLogger(__name__)


class MessageController(CRUDBase[MessageRecord, MessageCreate, dict]):
    def __init__(self):
        super().__init__(model=MessageRecord)

    async def send_message(self, sender_id: int, obj_in: MessageCreate) -> MessageRecord:
        data = obj_in.model_dump()
        data["sender_id"] = sender_id
        msg = MessageRecord(**data)
        await msg.save()

        # 尝试发送微信订阅通知给接收人
        await self._try_send_wx_notification(msg, sender_id)

        return msg

    async def _try_send_wx_notification(self, msg: MessageRecord, sender_id: int):
        """如果接收人绑定了微信 openid，尝试发送订阅消息通知"""
        template_id = settings.WECHAT_SUBSCRIBE_TEMPLATE_ID
        if not template_id or not msg.receiver_id:
            return

        try:
            receiver = await User.filter(id=msg.receiver_id).first()
            if not receiver or not receiver.openid:
                return

            sender = await User.filter(id=sender_id).first()
            sender_name = (sender.alias or sender.username) if sender else "系统"

            # 构造订阅消息模板数据
            wx_data = {
                "name1": {"value": sender_name},
                "thing2": {"value": (msg.content or "您收到一条新消息")[:20]},
            }
            page = f"pages/message/detail?ticket_id={msg.ticket_id}" if msg.ticket_id else ""

            await send_subscribe_message(
                openid=receiver.openid,
                template_id=template_id,
                data=wx_data,
                page=page,
            )
        except Exception as e:
            logger.error(f"发送微信订阅通知失败: {e}")

    async def get_ticket_messages(self, ticket_id: int, user_id: int = None):
        q = Q(ticket_id=ticket_id)
        if user_id:
            q &= Q(sender_id=user_id) | Q(receiver_id=user_id)
        messages = await MessageRecord.filter(q).order_by("created_at")
        result = []
        for msg in messages:
            d = await msg.to_dict()
            sender = await User.filter(id=msg.sender_id).first()
            d["sender_name"] = sender.alias or sender.username if sender else ""
            if msg.receiver_id:
                receiver = await User.filter(id=msg.receiver_id).first()
                d["receiver_name"] = receiver.alias or receiver.username if receiver else ""
            result.append(d)
        return result

    async def mark_as_read(self, message_ids: list[int], user_id: int):
        await MessageRecord.filter(id__in=message_ids, receiver_id=user_id).update(is_read=True)

    async def get_unread_count(self, user_id: int):
        return await MessageRecord.filter(receiver_id=user_id, is_read=False).count()


class CallController(CRUDBase[CallRecord, CallCreate, dict]):
    def __init__(self):
        super().__init__(model=CallRecord)

    async def initiate_call(self, caller_id: int, obj_in: CallCreate) -> CallRecord:
        room_id = f"room_{uuid.uuid4().hex[:12]}"
        call = CallRecord(
            ticket_id=obj_in.ticket_id,
            caller_id=caller_id,
            callee_id=obj_in.callee_id,
            status=CallStatus.INITIATING,
            room_id=room_id,
        )
        await call.save()
        return call

    async def update_call_status(self, call_id: int, status: str, **kwargs):
        call = await self.get(id=call_id)
        call.status = status
        for k, v in kwargs.items():
            if hasattr(call, k):
                setattr(call, k, v)
        await call.save()
        return call


message_controller = MessageController()
call_controller = CallController()
