import uuid
from datetime import datetime

from fastapi.exceptions import HTTPException
from tortoise.expressions import Q

from app.core.crud import CRUDBase
from app.models.admin import (
    AuditRecord,
    OrderFlow,
    OrderTicket,
    Region,
    User,
)
from app.models.enums import AuditResult, FlowAction, TicketStatus
from app.schemas.tickets import TicketCreate, TicketUpdate


def generate_ticket_no():
    now = datetime.now()
    return f"WO{now.strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"


def format_user_display(user):
    """Format user display as '姓名(用户名)' or just username"""
    if not user:
        return ""
    if user.alias and user.alias != user.username:
        return f"{user.alias}({user.username})"
    return user.username


class TicketController(CRUDBase[OrderTicket, TicketCreate, TicketUpdate]):
    def __init__(self):
        super().__init__(model=OrderTicket)

    async def create_ticket(self, obj_in: TicketCreate, submitter_id: int) -> OrderTicket:
        data = obj_in.model_dump()
        data["ticket_no"] = generate_ticket_no()
        data["submitter_id"] = submitter_id
        data["status"] = TicketStatus.DRAFT

        # Auto-fill salesman with submitter's display name if not provided
        if not data.get("salesman"):
            submitter = await User.filter(id=submitter_id).first()
            if submitter:
                data["salesman"] = format_user_display(submitter)

        # Auto-assign reviewer if region has a manager
        if data.get("region_id"):
            region = await Region.filter(id=data["region_id"]).first()
            if region and region.manager_id:
                pass  # Will be assigned during review

        ticket = OrderTicket(**data)
        await ticket.save()

        # Create flow record
        await OrderFlow.create(
            ticket_id=ticket.id,
            action=FlowAction.CREATE,
            from_status=None,
            to_status=TicketStatus.DRAFT,
            operator_id=submitter_id,
            remark="工单创建",
        )
        return ticket

    async def submit_ticket(self, ticket_id: int, submitter_id: int, remark: str = None) -> OrderTicket:
        ticket = await self.get(id=ticket_id)
        if ticket.status not in (TicketStatus.DRAFT, TicketStatus.REJECTED):
            raise HTTPException(status_code=400, detail="只有草稿或已驳回状态的工单才能提交")

        old_status = ticket.status
        ticket.status = TicketStatus.PENDING_REVIEW
        ticket.last_process_time = datetime.now()
        await ticket.save()

        action = FlowAction.RESUBMIT if old_status == TicketStatus.REJECTED else FlowAction.SUBMIT
        await OrderFlow.create(
            ticket_id=ticket_id,
            action=action,
            from_status=old_status,
            to_status=TicketStatus.PENDING_REVIEW,
            operator_id=submitter_id,
            remark=remark or ("重新提交工单" if old_status == TicketStatus.REJECTED else "提交工单"),
        )
        return ticket

    async def withdraw_ticket(self, ticket_id: int, operator_id: int, remark: str = None) -> OrderTicket:
        ticket = await self.get(id=ticket_id)
        if ticket.status != TicketStatus.PENDING_REVIEW:
            raise HTTPException(status_code=400, detail="只有待审核状态的工单才能撤回")

        if ticket.submitter_id != operator_id:
            raise HTTPException(status_code=403, detail="只有工单提交人才能撤回工单")

        old_status = ticket.status
        ticket.status = TicketStatus.DRAFT
        ticket.last_process_time = datetime.now()
        await ticket.save()

        await OrderFlow.create(
            ticket_id=ticket_id,
            action=FlowAction.WITHDRAW,
            from_status=old_status,
            to_status=TicketStatus.DRAFT,
            operator_id=operator_id,
            remark=remark or "撤回工单",
        )
        return ticket

    async def audit_ticket(self, ticket_id: int, reviewer_id: int, result: str,
                           reject_reason: str = None, remark: str = None, assign_to_id: int = None):
        ticket = await self.get(id=ticket_id)
        if ticket.status != TicketStatus.PENDING_REVIEW:
            raise HTTPException(status_code=400, detail="工单当前状态不允许审核")

        old_status = ticket.status

        if result == AuditResult.APPROVED:
            if assign_to_id:
                ticket.status = TicketStatus.ASSIGNED
                ticket.assignee_id = assign_to_id
            else:
                ticket.status = TicketStatus.PENDING_ASSIGN
            ticket.reviewer_id = reviewer_id
        elif result == AuditResult.REJECTED:
            if not reject_reason:
                raise HTTPException(status_code=400, detail="驳回必须填写原因")
            ticket.status = TicketStatus.REJECTED
            ticket.reviewer_id = reviewer_id
        else:
            raise HTTPException(status_code=400, detail="无效的审核结果")

        ticket.last_process_time = datetime.now()
        await ticket.save()

        # Create audit record
        await AuditRecord.create(
            ticket_id=ticket_id,
            reviewer_id=reviewer_id,
            result=result,
            reject_reason=reject_reason,
            remark=remark,
            assign_to_id=assign_to_id,
        )

        # Create flow record
        action = FlowAction.REVIEW_APPROVE if result == AuditResult.APPROVED else FlowAction.REVIEW_REJECT
        flow_remark = remark or reject_reason or ""
        if assign_to_id:
            target = await User.filter(id=assign_to_id).first()
            flow_remark += f" | 指派给 {format_user_display(target)}"
        await OrderFlow.create(
            ticket_id=ticket_id,
            action=action,
            from_status=old_status,
            to_status=ticket.status,
            operator_id=reviewer_id,
            remark=flow_remark,
        )
        return ticket

    async def assign_ticket(self, ticket_id: int, assignee_id: int, operator_id: int, remark: str = None):
        ticket = await self.get(id=ticket_id)
        # Allow re-assign from assigned status too (admin/reviewer can change assignment)
        if ticket.status not in (TicketStatus.PENDING_ASSIGN, TicketStatus.APPROVED, TicketStatus.ASSIGNED):
            raise HTTPException(status_code=400, detail="工单当前状态不允许指派")

        old_status = ticket.status
        old_assignee = ticket.assignee_id
        ticket.assignee_id = assignee_id
        ticket.status = TicketStatus.ASSIGNED
        ticket.last_process_time = datetime.now()
        await ticket.save()

        target = await User.filter(id=assignee_id).first()
        flow_remark = remark or ""
        if old_assignee and old_assignee != assignee_id:
            old_user = await User.filter(id=old_assignee).first()
            flow_remark += f" | 从 {format_user_display(old_user)} 重新指派给 {format_user_display(target)}"
        else:
            flow_remark += f" | 指派给 {format_user_display(target)}"

        await OrderFlow.create(
            ticket_id=ticket_id,
            action=FlowAction.ASSIGN,
            from_status=old_status,
            to_status=TicketStatus.ASSIGNED,
            operator_id=operator_id,
            remark=flow_remark,
        )
        return ticket

    async def transfer_ticket(self, ticket_id: int, transfer_to_id: int, operator_id: int, reason: str = None):
        ticket = await self.get(id=ticket_id)
        # Allow transfer from transferred status too (re-transfer)
        if ticket.status not in (TicketStatus.ASSIGNED, TicketStatus.PROCESSING, TicketStatus.TRANSFERRED):
            raise HTTPException(status_code=400, detail="工单当前状态不允许转派")

        old_assignee = ticket.assignee_id
        old_status = ticket.status
        ticket.assignee_id = transfer_to_id
        ticket.status = TicketStatus.TRANSFERRED
        ticket.last_process_time = datetime.now()
        await ticket.save()

        old_user = await User.filter(id=old_assignee).first() if old_assignee else None
        target = await User.filter(id=transfer_to_id).first()
        flow_remark = reason or ""
        flow_remark += f" | 从 {format_user_display(old_user)} 转派给 {format_user_display(target)}"

        await OrderFlow.create(
            ticket_id=ticket_id,
            action=FlowAction.TRANSFER,
            from_status=old_status,
            to_status=TicketStatus.TRANSFERRED,
            operator_id=operator_id,
            remark=flow_remark.strip(),
            transfer_to_id=transfer_to_id,
        )
        return ticket

    async def revert_to_review(self, ticket_id: int, operator_id: int, remark: str = None):
        """Admin/reviewer can revert completed ticket back to pending_review"""
        ticket = await self.get(id=ticket_id)
        if ticket.status != TicketStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="只有已完成的工单才能打回重审")

        old_status = ticket.status
        ticket.status = TicketStatus.PENDING_REVIEW
        ticket.assignee_id = None
        ticket.last_process_time = datetime.now()
        await ticket.save()

        await OrderFlow.create(
            ticket_id=ticket_id,
            action=FlowAction.RESUBMIT,
            from_status=old_status,
            to_status=TicketStatus.PENDING_REVIEW,
            operator_id=operator_id,
            remark=remark or "管理员打回重新审核",
        )
        return ticket

    async def update_status(self, ticket_id: int, new_status: str, operator_id: int, remark: str = None):
        ticket = await self.get(id=ticket_id)
        old_status = ticket.status

        valid_transitions = {
            TicketStatus.DRAFT: [TicketStatus.PENDING_REVIEW],
            TicketStatus.ASSIGNED: [TicketStatus.PROCESSING],
            TicketStatus.TRANSFERRED: [TicketStatus.PROCESSING, TicketStatus.COMPLETED],
            TicketStatus.PROCESSING: [TicketStatus.COMPLETED, TicketStatus.CLOSED],
            TicketStatus.COMPLETED: [TicketStatus.CLOSED, TicketStatus.PENDING_REVIEW],
            TicketStatus.REJECTED: [TicketStatus.DRAFT, TicketStatus.PENDING_REVIEW],
        }

        allowed = valid_transitions.get(old_status, [])
        if new_status not in allowed:
            raise HTTPException(status_code=400, detail=f"不允许从 {old_status} 转为 {new_status}")

        action_map = {
            TicketStatus.PROCESSING: FlowAction.START_PROCESS,
            TicketStatus.COMPLETED: FlowAction.COMPLETE,
            TicketStatus.CLOSED: FlowAction.CLOSE,
            TicketStatus.PENDING_REVIEW: FlowAction.RESUBMIT,
            TicketStatus.DRAFT: FlowAction.WITHDRAW,
        }

        ticket.status = new_status
        ticket.last_process_time = datetime.now()
        await ticket.save()

        await OrderFlow.create(
            ticket_id=ticket_id,
            action=action_map.get(new_status, FlowAction.ADD_REMARK),
            from_status=old_status,
            to_status=new_status,
            operator_id=operator_id,
            remark=remark or "",
        )
        return ticket

    async def get_flow_records(self, ticket_id: int):
        flows = await OrderFlow.filter(ticket_id=ticket_id).order_by("created_at")
        result = []
        for flow in flows:
            d = await flow.to_dict()
            operator = await User.filter(id=flow.operator_id).first()
            d["operator_name"] = format_user_display(operator)
            if flow.transfer_to_id:
                target = await User.filter(id=flow.transfer_to_id).first()
                d["transfer_to_name"] = format_user_display(target)
            result.append(d)
        return result

    async def get_audit_records(self, ticket_id: int):
        records = await AuditRecord.filter(ticket_id=ticket_id).order_by("created_at")
        result = []
        for record in records:
            d = await record.to_dict()
            reviewer = await User.filter(id=record.reviewer_id).first()
            d["reviewer_name"] = format_user_display(reviewer)
            result.append(d)
        return result


ticket_controller = TicketController()
