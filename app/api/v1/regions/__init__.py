from fastapi import APIRouter

from .regions import router

regions_router = APIRouter()
regions_router.include_router(router, tags=["行政区管理"])

__all__ = ["regions_router"]
