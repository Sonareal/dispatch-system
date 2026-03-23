from fastapi import APIRouter

from app.core.dependency import DependAuth, DependPermission

from .apis import apis_router
from .auditlog import auditlog_router
from .base import base_router
from .cities import cities_router
from .depts import depts_router
from .menus import menus_router
from .messages import messages_router
from .oplog import oplog_router
from .regions import regions_router
from .roles import roles_router
from .sysconfig import sysconfig_router
from .tickets import tickets_router
from .users import users_router
from .ocr import ocr_router
from .ws.signaling import router as ws_router

v1_router = APIRouter()

v1_router.include_router(base_router, prefix="/base")
v1_router.include_router(users_router, prefix="/user", dependencies=[DependPermission])
v1_router.include_router(roles_router, prefix="/role", dependencies=[DependPermission])
v1_router.include_router(menus_router, prefix="/menu", dependencies=[DependPermission])
v1_router.include_router(apis_router, prefix="/api", dependencies=[DependPermission])
v1_router.include_router(depts_router, prefix="/dept", dependencies=[DependPermission])
v1_router.include_router(auditlog_router, prefix="/auditlog", dependencies=[DependPermission])
v1_router.include_router(cities_router, prefix="/city", dependencies=[DependAuth])
v1_router.include_router(regions_router, prefix="/region", dependencies=[DependAuth])
v1_router.include_router(tickets_router, prefix="/ticket", dependencies=[DependAuth])
v1_router.include_router(messages_router, prefix="/message", dependencies=[DependAuth])
v1_router.include_router(oplog_router, prefix="/oplog", dependencies=[DependPermission])
v1_router.include_router(sysconfig_router, prefix="/sysconfig", dependencies=[DependPermission])
v1_router.include_router(ocr_router, prefix="/ocr", dependencies=[DependAuth])
v1_router.include_router(ws_router, prefix="/ws", tags=["WebSocket"])

# Public site config endpoint (no auth required, for login page etc.)
from app.models.admin import SystemConfig as _SC
from app.schemas.base import Success as _Suc

@v1_router.get("/site/config", summary="获取站点配置（公开）", tags=["公开接口"])
async def _get_site_config():
    objs = await _SC.filter(group="site").all()
    data = {obj.key: obj.value for obj in objs}
    return _Suc(data=data)
