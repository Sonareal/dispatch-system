from app.core.crud import CRUDBase
from app.models.admin import City, Region, UserCity
from app.schemas.cities import CityCreate, CityUpdate, RegionCreate, RegionUpdate


class CityController(CRUDBase[City, CityCreate, CityUpdate]):
    def __init__(self):
        super().__init__(model=City)

    async def get_user_cities(self, user_id: int):
        user_cities = await UserCity.filter(user_id=user_id).values_list("city_id", flat=True)
        return await City.filter(id__in=user_cities, is_active=True).order_by("order")

    async def add_user_city(self, user_id: int, city_id: int):
        obj, created = await UserCity.get_or_create(user_id=user_id, city_id=city_id)
        return obj

    async def remove_user_city(self, user_id: int, city_id: int):
        await UserCity.filter(user_id=user_id, city_id=city_id).delete()

    async def set_user_cities(self, user_id: int, city_ids: list[int]):
        await UserCity.filter(user_id=user_id).delete()
        for city_id in city_ids:
            await UserCity.create(user_id=user_id, city_id=city_id)


class RegionController(CRUDBase[Region, RegionCreate, RegionUpdate]):
    def __init__(self):
        super().__init__(model=Region)

    async def get_tree(self, city_id: int = None, parent_id: int = 0):
        q = {"parent_id": parent_id}
        if city_id:
            q["city_id"] = city_id
        regions = await Region.filter(**q).order_by("id")
        result = []
        for region in regions:
            item = await region.to_dict()
            children = await self.get_tree(city_id=city_id, parent_id=region.id)
            item["children"] = children
            result.append(item)
        return result

    async def get_region_with_manager(self, region_id: int):
        region = await self.get(id=region_id)
        return region


city_controller = CityController()
region_controller = RegionController()
