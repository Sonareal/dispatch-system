import os

from fastapi import APIRouter, Body, File, Query, UploadFile
from tortoise.expressions import Q

from app.models.admin import SystemConfig
from app.schemas.base import Success, SuccessExtra
from app.settings.config import settings

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


@router.post("/upload_image", summary="上传站点图片(logo/背景)")
async def upload_site_image(
    config_key: str = Body(..., description="配置键，如 site_logo, login_bg"),
    file: UploadFile = File(...),
):
    upload_dir = os.path.join(settings.UPLOAD_DIR, "site")
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1] if file.filename else ".png"
    filename = f"{config_key}{ext}"
    filepath = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    file_url = f"/uploads/site/{filename}"

    # Save to config
    obj, created = await SystemConfig.get_or_create(
        key=config_key,
        defaults={"value": file_url, "desc": f"站点图片: {config_key}", "group": "site"},
    )
    if not created:
        obj.value = file_url
        await obj.save()

    return Success(msg="上传成功", data={"url": file_url})


@router.get("/site", summary="获取站点配置（公开，无需登录）")
async def get_site_config():
    """返回所有 site 分组的配置，用于登录页等公开场景"""
    objs = await SystemConfig.filter(group="site").all()
    data = {obj.key: obj.value for obj in objs}
    return Success(data=data)
