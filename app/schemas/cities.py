from typing import Optional

from pydantic import BaseModel, Field


class CityCreate(BaseModel):
    name: str = Field(..., description="城市名称")
    code: str = Field(..., description="城市编码")
    is_active: Optional[bool] = True
    order: Optional[int] = 0


class CityUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    code: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None


class RegionCreate(BaseModel):
    name: str = Field(..., description="区域名称")
    code: Optional[str] = Field(None, description="区域编码")
    parent_id: Optional[int] = Field(0, description="父级ID")
    level: str = Field(..., description="层级: province/city/district/street")
    city_id: Optional[int] = Field(None, description="所属城市ID")
    manager_id: Optional[int] = Field(None, description="负责人ID")


class RegionUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    code: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[str] = None
    city_id: Optional[int] = None
    manager_id: Optional[int] = None
