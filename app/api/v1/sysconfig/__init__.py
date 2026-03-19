from fastapi import APIRouter

from .sysconfig import router

sysconfig_router = APIRouter()
sysconfig_router.include_router(router, tags=["系统配置"])

__all__ = ["sysconfig_router"]
