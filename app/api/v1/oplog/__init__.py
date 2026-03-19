from fastapi import APIRouter

from .oplog import router

oplog_router = APIRouter()
oplog_router.include_router(router, tags=["操作日志"])

__all__ = ["oplog_router"]
