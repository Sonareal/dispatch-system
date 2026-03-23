import logging
from typing import List

from fastapi import APIRouter, Body, Query
from tortoise.expressions import Q

from app.controllers.dept import dept_controller
from app.controllers.user import user_controller
from app.models.admin import Region, RegionManager
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.users import *

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/list", summary="查看用户列表")
async def list_user(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    username: str = Query("", description="用户名称，用于搜索"),
    email: str = Query("", description="邮箱地址"),
    dept_id: int = Query(None, description="部门ID"),
):
    q = Q()
    if username:
        q &= Q(username__contains=username)
    if email:
        q &= Q(email__contains=email)
    if dept_id is not None:
        q &= Q(dept_id=dept_id)
    total, user_objs = await user_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict(m2m=True, exclude_fields=["password"]) for obj in user_objs]
    for item in data:
        dept_id_val = item.pop("dept_id", None)
        item["dept"] = await (await dept_controller.get(id=dept_id_val)).to_dict() if dept_id_val else {}
        # Attach managed regions (from RegionManager table)
        rm_entries = await RegionManager.filter(user_id=item["id"]).all()
        region_ids = [rm.region_id for rm in rm_entries]
        managed_regions = await Region.filter(id__in=region_ids).all() if region_ids else []
        item["managed_regions"] = [{"id": r.id, "name": r.name, "level": r.level.value if hasattr(r.level, 'value') else str(r.level)} for r in managed_regions]

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看用户")
async def get_user(
    user_id: int = Query(..., description="用户ID"),
):
    user_obj = await user_controller.get(id=user_id)
    user_dict = await user_obj.to_dict(exclude_fields=["password"])
    return Success(data=user_dict)


@router.post("/create", summary="创建用户")
async def create_user(
    user_in: UserCreate,
):
    user = await user_controller.get_by_email(user_in.email)
    if user:
        return Fail(code=400, msg="The user with this email already exists in the system.")
    new_user = await user_controller.create_user(obj_in=user_in)
    await user_controller.update_roles(new_user, user_in.role_ids)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新用户")
async def update_user(
    user_in: UserUpdate,
):
    user = await user_controller.update(id=user_in.id, obj_in=user_in)
    await user_controller.update_roles(user, user_in.role_ids)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除用户")
async def delete_user(
    user_id: int = Query(..., description="用户ID"),
):
    await user_controller.remove(id=user_id)
    return Success(msg="Deleted Successfully")


@router.post("/reset_password", summary="重置密码")
async def reset_password(user_id: int = Body(..., description="用户ID", embed=True)):
    await user_controller.reset_password(user_id)
    return Success(msg="密码已重置为123456")


@router.get("/managed_regions", summary="获取用户负责的区域")
async def get_user_managed_regions(user_id: int = Query(..., description="用户ID")):
    rm_entries = await RegionManager.filter(user_id=user_id).all()
    region_ids = [rm.region_id for rm in rm_entries]
    regions = await Region.filter(id__in=region_ids).all() if region_ids else []
    data = [{"id": r.id, "name": r.name, "code": r.code, "level": r.level.value if hasattr(r.level, 'value') else str(r.level), "city_id": r.city_id} for r in regions]
    return Success(data=data)


@router.post("/set_managed_regions", summary="设置用户负责的区域")
async def set_user_managed_regions(
    user_id: int = Body(..., description="用户ID"),
    region_ids: List[int] = Body([], description="区域ID列表"),
):
    # Clear old entries for this user
    await RegionManager.filter(user_id=user_id).delete()

    # Create new entries
    for rid in region_ids:
        region = await Region.filter(id=rid).first()
        if region:
            await RegionManager.get_or_create(region_id=rid, user_id=user_id)

    return Success(msg="区域设置成功")


@router.post("/update_roles", summary="更新用户角色")
async def update_user_roles(
    user_id: int = Body(..., description="用户ID"),
    role_ids: List[int] = Body([], description="角色ID列表"),
):
    user = await user_controller.get(id=user_id)
    await user_controller.update_roles(user, role_ids)
    return Success(msg="角色更新成功")


@router.post("/toggle_active", summary="启用/禁用用户")
async def toggle_user_active(
    user_id: int = Body(..., description="用户ID"),
    is_active: bool = Body(..., description="是否启用"),
):
    user = await user_controller.get(id=user_id)
    user.is_active = is_active
    await user.save()
    return Success(msg="已启用" if is_active else "已禁用")
