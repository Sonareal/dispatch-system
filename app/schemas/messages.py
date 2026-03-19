from typing import Optional

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    ticket_id: int = Field(..., description="工单ID")
    receiver_id: Optional[int] = Field(None, description="接收人ID")
    msg_type: str = Field("text", description="消息类型: text/voice/image/system")
    content: Optional[str] = Field(None, description="消息内容")
    file_url: Optional[str] = Field(None, description="文件地址")
    voice_duration: Optional[int] = Field(None, description="语音时长(秒)")


class CallCreate(BaseModel):
    ticket_id: int = Field(..., description="工单ID")
    callee_id: int = Field(..., description="接听人ID")
