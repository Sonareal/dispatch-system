from fastapi import APIRouter

from .cities import router

cities_router = APIRouter()
cities_router.include_router(router, tags=["城市管理"])

__all__ = ["cities_router"]
