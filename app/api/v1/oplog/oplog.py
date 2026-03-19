from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.models.admin import OperationLog
from app.schemas.base import SuccessExtra

router = APIRouter()


@router.get("/list", summary="获取操作日志列表")
async def list_operation_logs(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    module: str = Query("", description="模块"),
    action: str = Query("", description="操作类型"),
    operator_name: str = Query("", description="操作人"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    q = Q()
    if module:
        q &= Q(module__contains=module)
    if action:
        q &= Q(action__contains=action)
    if operator_name:
        q &= Q(operator_name__contains=operator_name)
    if start_time:
        q &= Q(created_at__gte=start_time)
    if end_time:
        q &= Q(created_at__lte=end_time)

    total = await OperationLog.filter(q).count()
    objs = await OperationLog.filter(q).offset((page - 1) * page_size).limit(page_size).order_by("-created_at")
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)
