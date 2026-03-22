import shutil

from aerich import Command
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from tortoise.expressions import Q

from app.api import api_router
from app.controllers.api import api_controller
from app.controllers.user import UserCreate, user_controller
from app.core.exceptions import (
    DoesNotExist,
    DoesNotExistHandle,
    HTTPException,
    HttpExcHandle,
    IntegrityError,
    IntegrityHandle,
    RequestValidationError,
    RequestValidationHandle,
    ResponseValidationError,
    ResponseValidationHandle,
)
from app.log import logger
from app.models.admin import Api, City, Menu, Region, RegionManager, Role
from app.models.enums import RegionLevel
from app.schemas.menus import MenuType
from app.settings.config import settings

from .middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware


def make_middlewares():
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
        ),
        Middleware(BackGroundTaskMiddleware),
        Middleware(
            HttpAuditLogMiddleware,
            methods=["GET", "POST", "PUT", "DELETE"],
            exclude_paths=[
                "/api/v1/base/access_token",
                "/docs",
                "/openapi.json",
                "/uploads",
            ],
        ),
    ]
    return middleware


def register_exceptions(app: FastAPI):
    app.add_exception_handler(DoesNotExist, DoesNotExistHandle)
    app.add_exception_handler(HTTPException, HttpExcHandle)
    app.add_exception_handler(IntegrityError, IntegrityHandle)
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)
    app.add_exception_handler(ResponseValidationError, ResponseValidationHandle)


def register_routers(app: FastAPI, prefix: str = "/api"):
    app.include_router(api_router, prefix=prefix)

    import os
    from fastapi.responses import FileResponse

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    @app.get("/uploads/{file_path:path}")
    async def serve_upload(file_path: str):
        full_path = os.path.join(settings.UPLOAD_DIR, file_path)
        if os.path.isfile(full_path):
            return FileResponse(full_path)
        return JSONResponse(content={"code": 404, "msg": "File not found"}, status_code=404)


async def init_superuser():
    user = await user_controller.model.exists()
    if not user:
        await user_controller.create_user(
            UserCreate(
                username="admin",
                email="admin@admin.com",
                password="123456",
                is_active=True,
                is_superuser=True,
            )
        )


async def init_menus():
    menus = await Menu.exists()
    if not menus:
        # 工作台已在前端 basicRoutes 中定义，无需重复创建菜单

        # Ticket management
        ticket_menu = await Menu.create(
            menu_type=MenuType.CATALOG, name="工单管理", path="/ticket", order=1,
            parent_id=0, icon="mdi:clipboard-text-outline", is_hidden=False,
            component="Layout", keepalive=False, redirect="/ticket/list",
        )
        await Menu.bulk_create([
            Menu(menu_type=MenuType.MENU, name="工单列表", path="list", order=1,
                 parent_id=ticket_menu.id, icon="mdi:format-list-bulleted",
                 is_hidden=False, component="/ticket/list", keepalive=False),
            Menu(menu_type=MenuType.MENU, name="待审核", path="pending-review", order=2,
                 parent_id=ticket_menu.id, icon="mdi:file-document-edit-outline",
                 is_hidden=False, component="/ticket/pending-review", keepalive=False),
            Menu(menu_type=MenuType.MENU, name="我的工单", path="my-tickets", order=3,
                 parent_id=ticket_menu.id, icon="mdi:account-file-text-outline",
                 is_hidden=False, component="/ticket/my-tickets", keepalive=False),
            Menu(menu_type=MenuType.MENU, name="我负责的", path="my-assigned", order=4,
                 parent_id=ticket_menu.id, icon="mdi:account-hard-hat",
                 is_hidden=False, component="/ticket/my-assigned", keepalive=False),
        ])

        # Communication
        msg_menu = await Menu.create(
            menu_type=MenuType.CATALOG, name="沟通管理", path="/communication", order=2,
            parent_id=0, icon="mdi:message-text-outline", is_hidden=False,
            component="Layout", keepalive=False, redirect="/communication/messages",
        )
        await Menu.bulk_create([
            Menu(menu_type=MenuType.MENU, name="消息记录", path="messages", order=1,
                 parent_id=msg_menu.id, icon="mdi:chat-outline",
                 is_hidden=False, component="/communication/messages", keepalive=False),
            Menu(menu_type=MenuType.MENU, name="语音记录", path="voice", order=2,
                 parent_id=msg_menu.id, icon="mdi:microphone-outline",
                 is_hidden=False, component="/communication/voice", keepalive=False),
            Menu(menu_type=MenuType.MENU, name="通话记录", path="calls", order=3,
                 parent_id=msg_menu.id, icon="mdi:phone-outline",
                 is_hidden=False, component="/communication/calls", keepalive=False),
        ])

        # Area management
        area_menu = await Menu.create(
            menu_type=MenuType.CATALOG, name="区域管理", path="/area", order=3,
            parent_id=0, icon="mdi:map-marker-radius-outline", is_hidden=False,
            component="Layout", keepalive=False, redirect="/area/city",
        )
        await Menu.bulk_create([
            Menu(menu_type=MenuType.MENU, name="城市管理", path="city", order=1,
                 parent_id=area_menu.id, icon="mdi:city-variant-outline",
                 is_hidden=False, component="/area/city", keepalive=False),
            Menu(menu_type=MenuType.MENU, name="行政区管理", path="region", order=2,
                 parent_id=area_menu.id, icon="mdi:map-outline",
                 is_hidden=False, component="/area/region", keepalive=False),
        ])

        # System management
        sys_menu = await Menu.create(
            menu_type=MenuType.CATALOG, name="系统管理", path="/system", order=10,
            parent_id=0, icon="carbon:gui-management", is_hidden=False,
            component="Layout", keepalive=False, redirect="/system/user",
        )
        await Menu.bulk_create([
            Menu(menu_type=MenuType.MENU, name="用户管理", path="user", order=1,
                 parent_id=sys_menu.id, icon="material-symbols:person-outline-rounded",
                 is_hidden=False, component="/system/user", keepalive=False),
            Menu(menu_type=MenuType.MENU, name="角色管理", path="role", order=2,
                 parent_id=sys_menu.id, icon="carbon:user-role",
                 is_hidden=False, component="/system/role", keepalive=False),
            Menu(menu_type=MenuType.MENU, name="菜单管理", path="menu", order=3,
                 parent_id=sys_menu.id, icon="material-symbols:list-alt-outline",
                 is_hidden=False, component="/system/menu", keepalive=False),
            Menu(menu_type=MenuType.MENU, name="API管理", path="api", order=4,
                 parent_id=sys_menu.id, icon="ant-design:api-outlined",
                 is_hidden=False, component="/system/api", keepalive=False),
            Menu(menu_type=MenuType.MENU, name="部门管理", path="dept", order=5,
                 parent_id=sys_menu.id, icon="mingcute:department-line",
                 is_hidden=False, component="/system/dept", keepalive=False),
            Menu(menu_type=MenuType.MENU, name="审计日志", path="auditlog", order=6,
                 parent_id=sys_menu.id, icon="ph:clipboard-text-bold",
                 is_hidden=False, component="/system/auditlog", keepalive=False),
            Menu(menu_type=MenuType.MENU, name="操作日志", path="oplog", order=7,
                 parent_id=sys_menu.id, icon="mdi:history",
                 is_hidden=False, component="/system/oplog", keepalive=False),
            Menu(menu_type=MenuType.MENU, name="系统配置", path="config", order=8,
                 parent_id=sys_menu.id, icon="mdi:cog-outline",
                 is_hidden=False, component="/system/config", keepalive=False),
        ])


async def init_apis():
    apis = await api_controller.model.exists()
    if not apis:
        await api_controller.refresh_api()


async def init_db():
    command = Command(tortoise_config=settings.TORTOISE_ORM)
    try:
        await command.init_db(safe=True)
    except FileExistsError:
        pass

    await command.init()
    try:
        await command.migrate()
    except AttributeError:
        logger.warning("unable to retrieve model history from database, model history will be created from scratch")
        shutil.rmtree("migrations")
        await command.init_db(safe=True)

    await command.upgrade(run_in_transaction=True)


async def init_roles():
    roles = await Role.exists()
    if not roles:
        super_admin_role = await Role.create(name="超级管理员", code="super_admin", desc="超级管理员角色")
        admin_role = await Role.create(name="管理员", code="admin", desc="管理员角色")
        reviewer_role = await Role.create(name="审核人员", code="reviewer", desc="审核人员角色")
        region_rep_role = await Role.create(name="区域代表", code="region_rep", desc="区域代表角色")
        front_staff_role = await Role.create(name="前端服务人员", code="front_staff", desc="前端服务人员角色")

        all_apis = await Api.all()
        await super_admin_role.apis.add(*all_apis)
        await admin_role.apis.add(*all_apis)

        all_menus = await Menu.all()
        await super_admin_role.menus.add(*all_menus)
        await admin_role.menus.add(*all_menus)

        # Reviewer gets ticket + message + workbench menus
        ticket_parent = await Menu.filter(path="/ticket").first()
        msg_parent = await Menu.filter(path="/communication").first()
        reviewer_menus = await Menu.filter(
            Q(path="/workbench") |
            Q(id=ticket_parent.id) | Q(parent_id=ticket_parent.id) |
            Q(id=msg_parent.id) | Q(parent_id=msg_parent.id)
        )
        await reviewer_role.menus.add(*reviewer_menus)
        reviewer_apis = await Api.filter(Q(tags__in=["基础模块", "工单管理", "消息沟通"]) | Q(method="GET"))
        await reviewer_role.apis.add(*reviewer_apis)

        # Region rep gets same as reviewer
        await region_rep_role.menus.add(*reviewer_menus)
        await region_rep_role.apis.add(*reviewer_apis)

        # Front staff gets workbench + my tickets
        staff_menus = await Menu.filter(
            Q(path="/workbench") |
            Q(id=ticket_parent.id) |
            Q(path__in=["list", "my-tickets"], parent_id=ticket_parent.id)
        )
        await front_staff_role.menus.add(*staff_menus)
        basic_apis = await Api.filter(Q(method="GET") | Q(tags="基础模块"))
        await front_staff_role.apis.add(*basic_apis)


async def init_demo_cities():
    cities = await City.exists()
    if not cities:
        # ====== 北京市 ======
        bj_city = await City.create(name="北京市", code="110000", is_active=True, order=1)
        bj_prov = await Region.create(name="北京市", code="110000", parent_id=0, level=RegionLevel.PROVINCE, city_id=bj_city.id)
        bj_districts = [
            ("东城区", "110101"), ("西城区", "110102"), ("朝阳区", "110105"),
            ("丰台区", "110106"), ("石景山区", "110107"), ("海淀区", "110108"),
            ("门头沟区", "110109"), ("房山区", "110111"), ("通州区", "110112"),
            ("顺义区", "110113"), ("昌平区", "110114"), ("大兴区", "110115"),
            ("怀柔区", "110116"), ("平谷区", "110117"), ("密云区", "110118"),
            ("延庆区", "110119"),
        ]
        await Region.bulk_create([
            Region(name=n, code=c, parent_id=bj_prov.id, level=RegionLevel.DISTRICT, city_id=bj_city.id)
            for n, c in bj_districts
        ])

        # ====== 上海市 ======
        sh_city = await City.create(name="上海市", code="310000", is_active=True, order=2)
        sh_prov = await Region.create(name="上海市", code="310000", parent_id=0, level=RegionLevel.PROVINCE, city_id=sh_city.id)
        sh_districts = [
            ("黄浦区", "310101"), ("徐汇区", "310104"), ("长宁区", "310105"),
            ("静安区", "310106"), ("普陀区", "310107"), ("虹口区", "310109"),
            ("杨浦区", "310110"), ("闵行区", "310112"), ("宝山区", "310113"),
            ("嘉定区", "310114"), ("浦东新区", "310115"), ("金山区", "310116"),
            ("松江区", "310117"), ("青浦区", "310118"), ("奉贤区", "310120"),
            ("崇明区", "310151"),
        ]
        await Region.bulk_create([
            Region(name=n, code=c, parent_id=sh_prov.id, level=RegionLevel.DISTRICT, city_id=sh_city.id)
            for n, c in sh_districts
        ])

        # ====== 广州市 ======
        gz_city = await City.create(name="广州市", code="440100", is_active=True, order=3)
        gd_prov = await Region.create(name="广东省", code="440000", parent_id=0, level=RegionLevel.PROVINCE, city_id=gz_city.id)
        gz_muni = await Region.create(name="广州市", code="440100", parent_id=gd_prov.id, level=RegionLevel.CITY, city_id=gz_city.id)
        gz_districts = [
            ("荔湾区", "440103"), ("越秀区", "440104"), ("海珠区", "440105"),
            ("天河区", "440106"), ("白云区", "440111"), ("黄埔区", "440112"),
            ("番禺区", "440113"), ("花都区", "440114"), ("南沙区", "440115"),
            ("从化区", "440117"), ("增城区", "440118"),
        ]
        await Region.bulk_create([
            Region(name=n, code=c, parent_id=gz_muni.id, level=RegionLevel.DISTRICT, city_id=gz_city.id)
            for n, c in gz_districts
        ])

        # ====== 深圳市 ======
        sz_city = await City.create(name="深圳市", code="440300", is_active=True, order=4)
        # 深圳也属于广东省，但作为独立城市管理，也需要独立的省级region
        gd_prov_sz = await Region.create(name="广东省", code="440000_sz", parent_id=0, level=RegionLevel.PROVINCE, city_id=sz_city.id)
        sz_muni = await Region.create(name="深圳市", code="440300", parent_id=gd_prov_sz.id, level=RegionLevel.CITY, city_id=sz_city.id)
        sz_districts = [
            ("罗湖区", "440303"), ("福田区", "440304"), ("南山区", "440305"),
            ("宝安区", "440306"), ("龙岗区", "440307"), ("盐田区", "440308"),
            ("龙华区", "440309"), ("坪山区", "440310"), ("光明区", "440311"),
            ("大鹏新区", "440312"),
        ]
        await Region.bulk_create([
            Region(name=n, code=c, parent_id=sz_muni.id, level=RegionLevel.DISTRICT, city_id=sz_city.id)
            for n, c in sz_districts
        ])

        logger.info("Initialized cities and regions: 北京(16区), 上海(16区), 广州(11区), 深圳(10区)")


async def init_test_users():
    from app.models.admin import User, UserCity
    test_user = await User.filter(username="reviewer01").first()
    if test_user:
        return

    city = await City.filter(code="110000").first()
    if not city:
        return

    regions = await Region.filter(city_id=city.id, level=RegionLevel.DISTRICT)
    region_map = {r.name: r for r in regions}
    hd = region_map.get("海淀区")
    cy = region_map.get("朝阳区")
    ft = region_map.get("丰台区")

    reviewer_role = await Role.filter(code="reviewer").first()
    region_rep_role = await Role.filter(code="region_rep").first()
    front_staff_role = await Role.filter(code="front_staff").first()

    # Create reviewer
    reviewer = await user_controller.create_user(UserCreate(
        username="reviewer01", email="reviewer01@test.com", password="123456",
        is_active=True, is_superuser=False,
    ))
    reviewer.alias = "审核员张三"
    reviewer.phone = "13800000001"
    reviewer.default_city_id = city.id
    await reviewer.save()
    if reviewer_role:
        await reviewer.roles.add(reviewer_role)
    await UserCity.create(user_id=reviewer.id, city_id=city.id)

    # Create region reps - one per district
    rep_hd = await user_controller.create_user(UserCreate(
        username="rep_haidian", email="rep_hd@test.com", password="123456",
        is_active=True, is_superuser=False,
    ))
    rep_hd.alias = "海淀代表李四"
    rep_hd.phone = "13800000002"
    rep_hd.default_city_id = city.id
    await rep_hd.save()
    if region_rep_role:
        await rep_hd.roles.add(region_rep_role)
    await UserCity.create(user_id=rep_hd.id, city_id=city.id)
    if hd:
        await RegionManager.get_or_create(region_id=hd.id, user_id=rep_hd.id)

    rep_cy = await user_controller.create_user(UserCreate(
        username="rep_chaoyang", email="rep_cy@test.com", password="123456",
        is_active=True, is_superuser=False,
    ))
    rep_cy.alias = "朝阳代表王五"
    rep_cy.phone = "13800000003"
    rep_cy.default_city_id = city.id
    await rep_cy.save()
    if region_rep_role:
        await rep_cy.roles.add(region_rep_role)
    await UserCity.create(user_id=rep_cy.id, city_id=city.id)
    if cy:
        await RegionManager.get_or_create(region_id=cy.id, user_id=rep_cy.id)

    rep_ft = await user_controller.create_user(UserCreate(
        username="rep_fengtai", email="rep_ft@test.com", password="123456",
        is_active=True, is_superuser=False,
    ))
    rep_ft.alias = "丰台代表赵六"
    rep_ft.phone = "13800000004"
    rep_ft.default_city_id = city.id
    await rep_ft.save()
    if region_rep_role:
        await rep_ft.roles.add(region_rep_role)
    await UserCity.create(user_id=rep_ft.id, city_id=city.id)
    if ft:
        await RegionManager.get_or_create(region_id=ft.id, user_id=rep_ft.id)

    # Create front staff
    staff1 = await user_controller.create_user(UserCreate(
        username="staff01", email="staff01@test.com", password="123456",
        is_active=True, is_superuser=False,
    ))
    staff1.alias = "前端服务员孙七"
    staff1.phone = "13800000005"
    staff1.default_city_id = city.id
    await staff1.save()
    if front_staff_role:
        await staff1.roles.add(front_staff_role)
    await UserCity.create(user_id=staff1.id, city_id=city.id)

    staff2 = await user_controller.create_user(UserCreate(
        username="staff02", email="staff02@test.com", password="123456",
        is_active=True, is_superuser=False,
    ))
    staff2.alias = "前端服务员周八"
    staff2.phone = "13800000006"
    staff2.default_city_id = city.id
    await staff2.save()
    if front_staff_role:
        await staff2.roles.add(front_staff_role)
    await UserCity.create(user_id=staff2.id, city_id=city.id)

    logger.info("Test users created: reviewer01, rep_haidian, rep_chaoyang, rep_fengtai, staff01, staff02 (password: 123456)")


async def init_data():
    await init_db()
    await init_superuser()
    await init_menus()
    await init_apis()
    await init_roles()
    await init_demo_cities()
    await init_test_users()
