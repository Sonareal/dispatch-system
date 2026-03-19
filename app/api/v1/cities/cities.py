from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.city import city_controller
from app.core.ctx import CTX_USER_ID
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.cities import CityCreate, CityUpdate

router = APIRouter()


@router.get("/list", summary="获取城市列表")
async def list_cities(
    page: int = Query(1, description="页码"),
    page_size: int = Query(100, description="每页数量"),
    name: str = Query("", description="城市名称"),
    is_active: bool = Query(None, description="是否启用"),
):
    q = Q()
    if name:
        q &= Q(name__contains=name)
    if is_active is not None:
        q &= Q(is_active=is_active)
    total, objs = await city_controller.list(page=page, page_size=page_size, search=q, order=["order", "id"])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="获取城市详情")
async def get_city(city_id: int = Query(..., description="城市ID")):
    obj = await city_controller.get(id=city_id)
    return Success(data=await obj.to_dict())


@router.post("/create", summary="创建城市")
async def create_city(city_in: CityCreate):
    obj = await city_controller.create(city_in)
    return Success(msg="创建成功", data=await obj.to_dict())


@router.post("/update", summary="更新城市")
async def update_city(city_in: CityUpdate):
    obj = await city_controller.update(id=city_in.id, obj_in=city_in)
    return Success(msg="更新成功", data=await obj.to_dict())


@router.delete("/delete", summary="删除城市")
async def delete_city(city_id: int = Query(..., description="城市ID")):
    await city_controller.remove(id=city_id)
    return Success(msg="删除成功")


@router.get("/user_cities", summary="获取用户城市列表")
async def get_user_cities():
    user_id = CTX_USER_ID.get()
    cities = await city_controller.get_user_cities(user_id)
    data = [await c.to_dict() for c in cities]
    return Success(data=data)


@router.post("/set_user_cities", summary="设置用户城市")
async def set_user_cities(user_id: int, city_ids: list[int]):
    await city_controller.set_user_cities(user_id, city_ids)
    return Success(msg="设置成功")
