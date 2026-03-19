import os

from fastapi import APIRouter, File, Query, UploadFile
from tortoise.expressions import Q

from app.controllers.ticket import ticket_controller
from app.core.ctx import CTX_USER_ID
from app.models.admin import OrderTicket, User
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.tickets import (
    TicketAssign,
    TicketAudit,
    TicketCreate,
    TicketStatusUpdate,
    TicketTransfer,
    TicketUpdate,
)
from app.settings.config import settings

router = APIRouter()


@router.post("/create", summary="创建工单")
async def create_ticket(ticket_in: TicketCreate):
    user_id = CTX_USER_ID.get()
    ticket = await ticket_controller.create_ticket(ticket_in, submitter_id=user_id)
    return Success(msg="工单创建成功", data=await ticket.to_dict())


@router.get("/list", summary="查询工单列表")
async def list_tickets(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    ticket_no: str = Query("", description="工单号"),
    customer_name: str = Query("", description="客户姓名"),
    customer_phone: str = Query("", description="联系电话"),
    status: str = Query("", description="工单状态"),
    city_id: int = Query(None, description="城市ID"),
    submitter_id: int = Query(None, description="提交人ID"),
    assignee_id: int = Query(None, description="处理人ID"),
    my_tickets: bool = Query(False, description="仅我的工单"),
):
    user_id = CTX_USER_ID.get()
    q = Q()
    if ticket_no:
        q &= Q(ticket_no__contains=ticket_no)
    if customer_name:
        q &= Q(customer_name__contains=customer_name)
    if customer_phone:
        q &= Q(customer_phone__contains=customer_phone)
    if status:
        q &= Q(status=status)
    if city_id is not None:
        q &= Q(city_id=city_id)
    if submitter_id is not None:
        q &= Q(submitter_id=submitter_id)
    if assignee_id is not None:
        q &= Q(assignee_id=assignee_id)
    if my_tickets:
        q &= Q(submitter_id=user_id)

    total, objs = await ticket_controller.list(
        page=page, page_size=page_size, search=q, order=["-created_at"]
    )
    data = []
    for obj in objs:
        d = await obj.to_dict()
        # Add submitter/assignee names
        submitter = await User.filter(id=obj.submitter_id).first()
        d["submitter_name"] = submitter.alias or submitter.username if submitter else ""
        if obj.assignee_id:
            assignee = await User.filter(id=obj.assignee_id).first()
            d["assignee_name"] = assignee.alias or assignee.username if assignee else ""
        else:
            d["assignee_name"] = ""
        data.append(d)
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查询工单详情")
async def get_ticket(ticket_id: int = Query(..., description="工单ID")):
    obj = await ticket_controller.get(id=ticket_id)
    data = await obj.to_dict()

    # Add related info
    submitter = await User.filter(id=obj.submitter_id).first()
    data["submitter_name"] = submitter.alias or submitter.username if submitter else ""
    if obj.assignee_id:
        assignee = await User.filter(id=obj.assignee_id).first()
        data["assignee_name"] = assignee.alias or assignee.username if assignee else ""
    else:
        data["assignee_name"] = ""

    # Flow records
    data["flow_records"] = await ticket_controller.get_flow_records(ticket_id)
    data["audit_records"] = await ticket_controller.get_audit_records(ticket_id)

    return Success(data=data)


@router.post("/update", summary="更新工单信息")
async def update_ticket(ticket_in: TicketUpdate):
    obj = await ticket_controller.update(id=ticket_in.id, obj_in=ticket_in)
    return Success(msg="更新成功", data=await obj.to_dict())


@router.post("/audit", summary="审核工单")
async def audit_ticket(audit_in: TicketAudit):
    user_id = CTX_USER_ID.get()
    ticket = await ticket_controller.audit_ticket(
        ticket_id=audit_in.ticket_id,
        reviewer_id=user_id,
        result=audit_in.result,
        reject_reason=audit_in.reject_reason,
        remark=audit_in.remark,
        assign_to_id=audit_in.assign_to_id,
    )
    return Success(msg="审核完成", data=await ticket.to_dict())


@router.post("/assign", summary="指派工单")
async def assign_ticket(assign_in: TicketAssign):
    user_id = CTX_USER_ID.get()
    ticket = await ticket_controller.assign_ticket(
        ticket_id=assign_in.ticket_id,
        assignee_id=assign_in.assignee_id,
        operator_id=user_id,
        remark=assign_in.remark,
    )
    return Success(msg="指派成功", data=await ticket.to_dict())


@router.post("/transfer", summary="转派工单")
async def transfer_ticket(transfer_in: TicketTransfer):
    user_id = CTX_USER_ID.get()
    ticket = await ticket_controller.transfer_ticket(
        ticket_id=transfer_in.ticket_id,
        transfer_to_id=transfer_in.transfer_to_id,
        operator_id=user_id,
        reason=transfer_in.reason,
    )
    return Success(msg="转派成功", data=await ticket.to_dict())


@router.post("/update_status", summary="更新工单状态")
async def update_ticket_status(status_in: TicketStatusUpdate):
    user_id = CTX_USER_ID.get()
    ticket = await ticket_controller.update_status(
        ticket_id=status_in.ticket_id,
        new_status=status_in.status,
        operator_id=user_id,
        remark=status_in.remark,
    )
    return Success(msg="状态更新成功", data=await ticket.to_dict())


@router.get("/flow_records", summary="获取工单流转记录")
async def get_flow_records(ticket_id: int = Query(..., description="工单ID")):
    records = await ticket_controller.get_flow_records(ticket_id)
    return Success(data=records)


@router.get("/audit_records", summary="获取审核记录")
async def get_audit_records(ticket_id: int = Query(..., description="工单ID")):
    records = await ticket_controller.get_audit_records(ticket_id)
    return Success(data=records)


@router.get("/pending_review", summary="获取待审核工单列表")
async def pending_review_tickets(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    city_id: int = Query(None, description="城市ID"),
):
    q = Q(status="pending_review")
    if city_id is not None:
        q &= Q(city_id=city_id)
    total, objs = await ticket_controller.list(
        page=page, page_size=page_size, search=q, order=["-created_at"]
    )
    data = []
    for obj in objs:
        d = await obj.to_dict()
        submitter = await User.filter(id=obj.submitter_id).first()
        d["submitter_name"] = submitter.alias or submitter.username if submitter else ""
        data.append(d)
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/my_assigned", summary="获取我负责的工单")
async def my_assigned_tickets(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    status: str = Query("", description="工单状态"),
):
    user_id = CTX_USER_ID.get()
    q = Q(assignee_id=user_id)
    if status:
        q &= Q(status=status)
    total, objs = await ticket_controller.list(
        page=page, page_size=page_size, search=q, order=["-created_at"]
    )
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/upload_voice", summary="上传语音文件")
async def upload_voice(ticket_id: int, file: UploadFile = File(...)):
    upload_dir = os.path.join(settings.UPLOAD_DIR, "voice")
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1] if file.filename else ".mp3"
    filename = f"voice_{ticket_id}_{os.urandom(4).hex()}{ext}"
    filepath = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    file_url = f"/uploads/voice/{filename}"

    ticket = await ticket_controller.get(id=ticket_id)
    ticket.voice_file = file_url
    await ticket.save()

    return Success(msg="上传成功", data={"file_url": file_url})


@router.post("/upload_attachment", summary="上传附件")
async def upload_attachment(ticket_id: int, file: UploadFile = File(...)):
    upload_dir = os.path.join(settings.UPLOAD_DIR, "attachments")
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    filename = f"attach_{ticket_id}_{os.urandom(4).hex()}{ext}"
    filepath = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    file_url = f"/uploads/attachments/{filename}"

    ticket = await ticket_controller.get(id=ticket_id)
    attachments = ticket.attachment or []
    attachments.append({"filename": file.filename, "url": file_url})
    ticket.attachment = attachments
    await ticket.save()

    return Success(msg="上传成功", data={"file_url": file_url, "filename": file.filename})


@router.get("/statistics", summary="工单统计")
async def ticket_statistics(city_id: int = Query(None, description="城市ID")):
    q = Q()
    if city_id is not None:
        q &= Q(city_id=city_id)

    total = await OrderTicket.filter(q).count()
    pending_review = await OrderTicket.filter(q & Q(status="pending_review")).count()
    processing = await OrderTicket.filter(q & Q(status="processing")).count()
    completed = await OrderTicket.filter(q & Q(status="completed")).count()
    rejected = await OrderTicket.filter(q & Q(status="rejected")).count()
    assigned = await OrderTicket.filter(q & Q(status__in=["assigned", "transferred"])).count()

    return Success(data={
        "total": total,
        "pending_review": pending_review,
        "processing": processing,
        "completed": completed,
        "rejected": rejected,
        "assigned": assigned,
    })
