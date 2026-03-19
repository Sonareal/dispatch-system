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


class TicketController(CRUDBase[OrderTicket, TicketCreate, TicketUpdate]):
    def __init__(self):
        super().__init__(model=OrderTicket)

    async def create_ticket(self, obj_in: TicketCreate, submitter_id: int) -> OrderTicket:
        data = obj_in.model_dump()
        data["ticket_no"] = generate_ticket_no()
        data["submitter_id"] = submitter_id
        data["status"] = TicketStatus.PENDING_REVIEW

        # Auto-fill salesman with submitter's name if not provided
        if not data.get("salesman"):
            submitter = await User.filter(id=submitter_id).first()
            if submitter:
                data["salesman"] = submitter.alias or submitter.username

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
            to_status=TicketStatus.PENDING_REVIEW,
            operator_id=submitter_id,
            remark="工单创建",
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
        await OrderFlow.create(
            ticket_id=ticket_id,
            action=action,
            from_status=old_status,
            to_status=ticket.status,
            operator_id=reviewer_id,
            remark=remark or reject_reason or "",
        )
        return ticket

    async def assign_ticket(self, ticket_id: int, assignee_id: int, operator_id: int, remark: str = None):
        ticket = await self.get(id=ticket_id)
        if ticket.status not in (TicketStatus.PENDING_ASSIGN, TicketStatus.APPROVED):
            raise HTTPException(status_code=400, detail="工单当前状态不允许指派")

        old_status = ticket.status
        ticket.assignee_id = assignee_id
        ticket.status = TicketStatus.ASSIGNED
        ticket.last_process_time = datetime.now()
        await ticket.save()

        await OrderFlow.create(
            ticket_id=ticket_id,
            action=FlowAction.ASSIGN,
            from_status=old_status,
            to_status=TicketStatus.ASSIGNED,
            operator_id=operator_id,
            remark=remark or f"指派给用户{assignee_id}",
        )
        return ticket

    async def transfer_ticket(self, ticket_id: int, transfer_to_id: int, operator_id: int, reason: str = None):
        ticket = await self.get(id=ticket_id)
        if ticket.status not in (TicketStatus.ASSIGNED, TicketStatus.PROCESSING):
            raise HTTPException(status_code=400, detail="工单当前状态不允许转派")

        old_assignee = ticket.assignee_id
        old_status = ticket.status
        ticket.assignee_id = transfer_to_id
        ticket.status = TicketStatus.TRANSFERRED
        ticket.last_process_time = datetime.now()
        await ticket.save()

        await OrderFlow.create(
            ticket_id=ticket_id,
            action=FlowAction.TRANSFER,
            from_status=old_status,
            to_status=TicketStatus.TRANSFERRED,
            operator_id=operator_id,
            remark=reason or f"从用户{old_assignee}转派给用户{transfer_to_id}",
            transfer_to_id=transfer_to_id,
        )
        return ticket

    async def update_status(self, ticket_id: int, new_status: str, operator_id: int, remark: str = None):
        ticket = await self.get(id=ticket_id)
        old_status = ticket.status

        valid_transitions = {
            TicketStatus.ASSIGNED: [TicketStatus.PROCESSING],
            TicketStatus.TRANSFERRED: [TicketStatus.PROCESSING],
            TicketStatus.PROCESSING: [TicketStatus.COMPLETED, TicketStatus.CLOSED],
            TicketStatus.COMPLETED: [TicketStatus.CLOSED],
            TicketStatus.REJECTED: [TicketStatus.PENDING_REVIEW],  # Resubmit
        }

        allowed = valid_transitions.get(old_status, [])
        if new_status not in allowed:
            raise HTTPException(status_code=400, detail=f"不允许从 {old_status} 转为 {new_status}")

        action_map = {
            TicketStatus.PROCESSING: FlowAction.START_PROCESS,
            TicketStatus.COMPLETED: FlowAction.COMPLETE,
            TicketStatus.CLOSED: FlowAction.CLOSE,
            TicketStatus.PENDING_REVIEW: FlowAction.RESUBMIT,
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
            d["operator_name"] = operator.alias or operator.username if operator else ""
            if flow.transfer_to_id:
                target = await User.filter(id=flow.transfer_to_id).first()
                d["transfer_to_name"] = target.alias or target.username if target else ""
            result.append(d)
        return result

    async def get_audit_records(self, ticket_id: int):
        records = await AuditRecord.filter(ticket_id=ticket_id).order_by("created_at")
        result = []
        for record in records:
            d = await record.to_dict()
            reviewer = await User.filter(id=record.reviewer_id).first()
            d["reviewer_name"] = reviewer.alias or reviewer.username if reviewer else ""
            result.append(d)
        return result


ticket_controller = TicketController()
