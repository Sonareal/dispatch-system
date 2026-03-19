from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.city import region_controller
from app.schemas.base import Success, SuccessExtra
from app.schemas.cities import RegionCreate, RegionUpdate

router = APIRouter()


@router.get("/list", summary="获取行政区列表")
async def list_regions(
    page: int = Query(1, description="页码"),
    page_size: int = Query(100, description="每页数量"),
    city_id: int = Query(None, description="城市ID"),
    parent_id: int = Query(None, description="父级ID"),
    level: str = Query(None, description="层级"),
    name: str = Query("", description="名称"),
):
    q = Q()
    if city_id is not None:
        q &= Q(city_id=city_id)
    if parent_id is not None:
        q &= Q(parent_id=parent_id)
    if level:
        q &= Q(level=level)
    if name:
        q &= Q(name__contains=name)
    total, objs = await region_controller.list(page=page, page_size=page_size, search=q, order=["id"])
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/tree", summary="获取行政区树")
async def get_region_tree(city_id: int = Query(None, description="城市ID")):
    tree = await region_controller.get_tree(city_id=city_id)
    return Success(data=tree)


@router.get("/get", summary="获取行政区详情")
async def get_region(region_id: int = Query(..., description="行政区ID")):
    obj = await region_controller.get(id=region_id)
    return Success(data=await obj.to_dict())


@router.post("/create", summary="创建行政区")
async def create_region(region_in: RegionCreate):
    obj = await region_controller.create(region_in)
    return Success(msg="创建成功", data=await obj.to_dict())


@router.post("/update", summary="更新行政区")
async def update_region(region_in: RegionUpdate):
    obj = await region_controller.update(id=region_in.id, obj_in=region_in)
    return Success(msg="更新成功", data=await obj.to_dict())


@router.delete("/delete", summary="删除行政区")
async def delete_region(region_id: int = Query(..., description="行政区ID")):
    await region_controller.remove(id=region_id)
    return Success(msg="删除成功")


@router.post("/set_manager", summary="设置区域负责人")
async def set_region_manager(region_id: int, manager_id: int):
    obj = await region_controller.update(id=region_id, obj_in={"manager_id": manager_id})
    return Success(msg="设置成功", data=await obj.to_dict())
