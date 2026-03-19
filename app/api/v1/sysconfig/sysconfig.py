from fastapi import APIRouter, Body, Query
from tortoise.expressions import Q

from app.models.admin import SystemConfig
from app.schemas.base import Success, SuccessExtra

router = APIRouter()


@router.get("/list", summary="获取系统配置列表")
async def list_configs(
    page: int = Query(1, description="页码"),
    page_size: int = Query(50, description="每页数量"),
    group: str = Query("", description="配置分组"),
    key: str = Query("", description="配置键"),
):
    q = Q()
    if group:
        q &= Q(group=group)
    if key:
        q &= Q(key__contains=key)
    total = await SystemConfig.filter(q).count()
    objs = await SystemConfig.filter(q).offset((page - 1) * page_size).limit(page_size).order_by("group", "key")
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="获取配置值")
async def get_config(key: str = Query(..., description="配置键")):
    obj = await SystemConfig.filter(key=key).first()
    if not obj:
        return Success(data=None)
    return Success(data=await obj.to_dict())


@router.post("/set", summary="设置配置")
async def set_config(
    key: str = Body(..., description="配置键"),
    value: str = Body(..., description="配置值"),
    desc: str = Body("", description="说明"),
    group: str = Body("", description="分组"),
):
    obj, created = await SystemConfig.get_or_create(
        key=key,
        defaults={"value": value, "desc": desc, "group": group},
    )
    if not created:
        obj.value = value
        if desc:
            obj.desc = desc
        if group:
            obj.group = group
        await obj.save()
    return Success(msg="设置成功", data=await obj.to_dict())


@router.delete("/delete", summary="删除配置")
async def delete_config(key: str = Query(..., description="配置键")):
    await SystemConfig.filter(key=key).delete()
    return Success(msg="删除成功")
