from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    customer_name: str = Field(..., description="客户姓名")
    customer_phone: str = Field(..., description="联系电话")
    id_card: Optional[str] = Field(None, description="身份证号")
    apply_amount: Optional[Decimal] = Field(None, description="申请金额")
    repayment_method: Optional[str] = Field(None, description="还款方式")
    address: Optional[str] = Field(None, description="详细地址")
    salesman: Optional[str] = Field(None, description="业务员")
    inspection_fee: Optional[Decimal] = Field(None, description="考察费")
    remark: Optional[str] = Field(None, description="备注")
    city_id: int = Field(..., description="城市ID")
    province_id: Optional[int] = Field(None, description="省ID")
    district_id: Optional[int] = Field(None, description="市/区ID")
    region_id: Optional[int] = Field(None, description="区域ID")


class TicketUpdate(BaseModel):
    id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    id_card: Optional[str] = None
    apply_amount: Optional[Decimal] = None
    repayment_method: Optional[str] = None
    address: Optional[str] = None
    salesman: Optional[str] = None
    inspection_fee: Optional[Decimal] = None
    remark: Optional[str] = None
    city_id: Optional[int] = None
    province_id: Optional[int] = None
    district_id: Optional[int] = None
    region_id: Optional[int] = None


class TicketAssign(BaseModel):
    ticket_id: int = Field(..., description="工单ID")
    assignee_id: int = Field(..., description="处理人ID")
    remark: Optional[str] = Field(None, description="备注")


class TicketTransfer(BaseModel):
    ticket_id: int = Field(..., description="工单ID")
    transfer_to_id: int = Field(..., description="转派目标人ID")
    reason: Optional[str] = Field(None, description="转派原因")


class TicketAudit(BaseModel):
    ticket_id: int = Field(..., description="工单ID")
    result: str = Field(..., description="审核结果: approved/rejected")
    reject_reason: Optional[str] = Field(None, description="驳回原因")
    remark: Optional[str] = Field(None, description="备注")
    assign_to_id: Optional[int] = Field(None, description="指派给")


class TicketStatusUpdate(BaseModel):
    ticket_id: int = Field(..., description="工单ID")
    status: str = Field(..., description="新状态")
    remark: Optional[str] = Field(None, description="备注")
