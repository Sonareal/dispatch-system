import os

from fastapi import APIRouter, File, Query, UploadFile
from tortoise.expressions import Q

from app.controllers.ticket import format_user_display, ticket_controller
from app.core.ctx import CTX_USER_ID
from app.models.admin import OrderTicket, Region, RegionManager, Role, User, UserCity
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.tickets import (
    TicketAssign,
    TicketAudit,
    TicketCreate,
    TicketStatusUpdate,
    TicketSubmit,
    TicketTransfer,
    TicketUpdate,
    TicketWithdraw,
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
        d["submitter_name"] = format_user_display(submitter)
        if obj.assignee_id:
            assignee = await User.filter(id=obj.assignee_id).first()
            d["assignee_name"] = format_user_display(assignee)
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
    data["submitter_name"] = format_user_display(submitter)
    if obj.assignee_id:
        assignee = await User.filter(id=obj.assignee_id).first()
        data["assignee_name"] = format_user_display(assignee)
    else:
        data["assignee_name"] = ""

    # Add city/region names
    if obj.city_id:
        from app.models.admin import City
        city = await City.filter(id=obj.city_id).first()
        data["city_name"] = city.name if city else ""
    else:
        data["city_name"] = ""

    if obj.region_id:
        region = await Region.filter(id=obj.region_id).first()
        data["region_name"] = region.name if region else ""
        # Build full region path (e.g. "北京市 > 西城区")
        if region:
            path_parts = [region.name]
            parent = await Region.filter(id=region.parent_id).first() if region.parent_id else None
            while parent:
                path_parts.insert(0, parent.name)
                parent = await Region.filter(id=parent.parent_id).first() if parent.parent_id else None
            data["region_path"] = " > ".join(path_parts)
        else:
            data["region_path"] = ""
    else:
        data["region_name"] = ""
        data["region_path"] = ""

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


@router.post("/submit", summary="提交工单审核")
async def submit_ticket(submit_in: TicketSubmit):
    user_id = CTX_USER_ID.get()
    ticket = await ticket_controller.submit_ticket(submit_in.ticket_id, user_id)
    return Success(msg="提交成功", data=await ticket.to_dict())


@router.post("/withdraw", summary="撤回工单")
async def withdraw_ticket(withdraw_in: TicketWithdraw):
    user_id = CTX_USER_ID.get()
    ticket = await ticket_controller.withdraw_ticket(withdraw_in.ticket_id, user_id)
    return Success(msg="撤回成功", data=await ticket.to_dict())


@router.post("/revert_to_review", summary="打回重新审核")
async def revert_to_review(data: TicketSubmit):
    user_id = CTX_USER_ID.get()
    ticket = await ticket_controller.revert_to_review(data.ticket_id, user_id, "管理员打回重审")
    return Success(msg="已打回重审", data=await ticket.to_dict())


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
        d["submitter_name"] = format_user_display(submitter)
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


@router.get("/assignable_users", summary="获取可指派用户列表(含工作负载)")
async def get_assignable_users(
    ticket_id: int = Query(None, description="工单ID(自动获取区域)"),
    city_id: int = Query(None, description="城市ID"),
    region_id: int = Query(None, description="区域ID"),
):
    """
    根据工单区域或指定城市/区域，返回可指派的区域代表列表。
    包含每个用户的角色、姓名、联系方式、所属区域、当前处理中的工单数量。
    默认按工作负载从低到高排序。
    """
    target_city_id = city_id
    target_region_id = region_id

    # 如果传了 ticket_id，自动获取工单的城市和区域
    if ticket_id:
        ticket = await OrderTicket.filter(id=ticket_id).first()
        if ticket:
            if not target_city_id:
                target_city_id = ticket.city_id
            if not target_region_id:
                target_region_id = ticket.region_id

    # 查找可指派用户：拥有 region_rep 或 reviewer 角色的用户
    assignable_roles = await Role.filter(code__in=["region_rep", "reviewer"]).all()
    role_ids = [r.id for r in assignable_roles]
    role_map = {r.id: r for r in assignable_roles}

    if not role_ids:
        return Success(data=[])

    # 找到拥有这些角色的用户
    candidate_users = await User.filter(
        roles__id__in=role_ids, is_active=True
    ).distinct().prefetch_related("roles")

    # 如果有城市过滤，进一步筛选属于该城市的用户
    if target_city_id:
        city_user_ids = await UserCity.filter(city_id=target_city_id).values_list("user_id", flat=True)
        candidate_users = [u for u in candidate_users if u.id in city_user_ids]

    # 获取所有区域信息，找出每个用户负责的区域
    all_regions = []
    if target_city_id:
        all_regions = await Region.filter(city_id=target_city_id).all()
    else:
        all_regions = await Region.all()

    # 建立 user_id -> region 的映射 (from RegionManager table)
    region_map_by_id = {r.id: r for r in all_regions}
    all_rm = await RegionManager.filter(region_id__in=[r.id for r in all_regions]).all()
    manager_region_map = {}
    for rm in all_rm:
        if rm.user_id not in manager_region_map:
            manager_region_map[rm.user_id] = []
        if rm.region_id in region_map_by_id:
            manager_region_map[rm.user_id].append(region_map_by_id[rm.region_id])
    # Also support old manager_id field for backward compat
    for r in all_regions:
        if r.manager_id:
            if r.manager_id not in manager_region_map:
                manager_region_map[r.manager_id] = []
            if r not in manager_region_map[r.manager_id]:
                manager_region_map[r.manager_id].append(r)

    # 获取每个用户正在处理的工单数 (status in processing, assigned, transferred)
    active_statuses = ["assigned", "processing", "transferred"]

    # ===== Geographic proximity helper =====
    # Use region codes to estimate distance. Codes like 110105 (朝阳), 110108 (海淀)
    # Closer code numbers = geographically closer areas
    target_region_code = None
    target_region = None
    if target_region_id:
        target_region = await Region.filter(id=target_region_id).first()
        if target_region and target_region.code:
            target_region_code = target_region.code.replace("_sz", "")  # clean up suffix

    def code_distance(code1, code2):
        """Estimate geographic proximity from region codes. Lower = closer."""
        if not code1 or not code2:
            return 999999
        try:
            # Compare numeric codes - same prefix = same parent region = closer
            c1, c2 = code1.replace("_sz", ""), code2.replace("_sz", "")
            # First check if same city-level prefix (first 4 digits)
            if c1[:4] == c2[:4]:
                return abs(int(c1) - int(c2))
            # Same province prefix (first 2 digits)
            if c1[:2] == c2[:2]:
                return abs(int(c1) - int(c2)) + 10000
            return abs(int(c1) - int(c2)) + 100000
        except (ValueError, TypeError):
            return 999999

    # ===== Build matching sets =====
    exact_match_ids = set()  # 精确匹配工单区域的负责人
    city_match_ids = set()   # 同城市的区域代表（非精确匹配）
    user_min_distance = {}   # user_id -> minimum geographic distance

    if target_region_id and target_region:
        # Exact match: managers of THIS specific region
        region_manager_user_ids = await RegionManager.filter(
            region_id=target_region_id
        ).values_list("user_id", flat=True)
        exact_match_ids.update(region_manager_user_ids)

        # Backward compat: also check Region.manager_id
        if target_region.manager_id:
            exact_match_ids.add(target_region.manager_id)

        # City-level match: managers of OTHER regions in the same city
        sibling_regions = await Region.filter(
            city_id=target_region.city_id
        ).exclude(id=target_region_id).all()

        sibling_map = {sr.id: sr for sr in sibling_regions}
        for sr in sibling_regions:
            if sr.manager_id and sr.manager_id not in exact_match_ids:
                city_match_ids.add(sr.manager_id)
                # Track min distance
                dist = code_distance(target_region_code, sr.code)
                if sr.manager_id not in user_min_distance or dist < user_min_distance[sr.manager_id]:
                    user_min_distance[sr.manager_id] = dist

        # Also check RegionManager for sibling regions
        sibling_region_ids = [sr.id for sr in sibling_regions]
        if sibling_region_ids:
            sibling_rms = await RegionManager.filter(
                region_id__in=sibling_region_ids
            ).all()
            for rm in sibling_rms:
                if rm.user_id not in exact_match_ids:
                    city_match_ids.add(rm.user_id)
                    sr = sibling_map.get(rm.region_id)
                    if sr:
                        dist = code_distance(target_region_code, sr.code)
                        if rm.user_id not in user_min_distance or dist < user_min_distance[rm.user_id]:
                            user_min_distance[rm.user_id] = dist

    # Only keep exact_match_ids that are actual candidates
    exact_match_ids = {uid for uid in exact_match_ids if any(u.id == uid for u in candidate_users)}

    result = []
    for user in candidate_users:
        # 工作负载：当前正在处理的工单数
        workload = await OrderTicket.filter(
            assignee_id=user.id, status__in=active_statuses
        ).count()

        # 用户角色
        user_roles = await user.roles.all()
        role_names = [r.name for r in user_roles]

        # 用户负责的区域
        managed_regions = manager_region_map.get(user.id, [])
        region_names = [r.name for r in managed_regions]

        # 匹配级别: 0=精确匹配, 1=同城匹配(有负责区域), 2=同城(无负责区域), 3=其他
        is_exact = user.id in exact_match_ids
        is_city = user.id in city_match_ids
        if is_exact:
            match_level = 0
            match_label = "精准匹配"
        elif is_city:
            match_level = 1
            match_label = "同城匹配"
        elif managed_regions:
            match_level = 2
            match_label = "有区域"
        else:
            match_level = 3
            match_label = ""

        geo_dist = user_min_distance.get(user.id, 999999)

        result.append({
            "id": user.id,
            "username": user.username,
            "alias": format_user_display(user),
            "phone": user.phone or "",
            "roles": role_names,
            "regions": region_names,
            "workload": workload,
            "is_region_match": is_exact or is_city,
            "is_exact_match": is_exact,
            "match_label": match_label,
            "recommended": False,
            "_match_level": match_level,
            "_geo_dist": geo_dist,
        })

    # 排序：精确匹配 > 同城(按地理距离) > 有区域 > 其他，同级别按工作负载从低到高
    result.sort(key=lambda x: (x["_match_level"], x["_geo_dist"], x["workload"]))

    # 标记推荐用户（排序后的第一个有区域的）
    if result:
        result[0]["recommended"] = True

    # 清理内部排序字段
    for r in result:
        del r["_match_level"]
        del r["_geo_dist"]

    return Success(data=result)


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
