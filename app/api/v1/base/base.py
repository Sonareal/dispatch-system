from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter

from app.controllers.user import user_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.admin import Api, Menu, Role, User
from app.schemas.base import Fail, Success
from app.schemas.login import *
from app.schemas.users import UpdatePassword
from app.settings import settings
from app.utils.jwt_utils import create_access_token
from app.utils.password import get_password_hash, verify_password

router = APIRouter()


@router.post("/access_token", summary="获取token")
async def login_access_token(credentials: CredentialsSchema):
    user: User = await user_controller.authenticate(credentials)
    await user_controller.update_last_login(user.id)
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + access_token_expires

    data = JWTOut(
        access_token=create_access_token(
            data=JWTPayload(
                user_id=user.id,
                username=user.username,
                is_superuser=user.is_superuser,
                exp=expire,
            )
        ),
        username=user.username,
    )
    return Success(data=data.model_dump())


@router.get("/userinfo", summary="查看用户信息", dependencies=[DependAuth])
async def get_userinfo():
    user_id = CTX_USER_ID.get()
    user_obj = await user_controller.get(id=user_id)
    data = await user_obj.to_dict(exclude_fields=["password"])
    # Generate avatar based on user's role
    roles = await user_obj.roles.all()
    role_codes = [r.code for r in roles]
    # Use role-based avatar colors
    if "super_admin" in role_codes or user_obj.is_superuser:
        avatar_color = "c62828"  # dark red
        avatar_icon = "SA"
    elif "admin" in role_codes:
        avatar_color = "1565c0"  # dark blue
        avatar_icon = "AD"
    elif "reviewer" in role_codes:
        avatar_color = "6a1b9a"  # purple
        avatar_icon = "RV"
    elif "region_rep" in role_codes:
        avatar_color = "2e7d32"  # green
        avatar_icon = "RP"
    elif "front_staff" in role_codes:
        avatar_color = "e65100"  # orange
        avatar_icon = "FS"
    else:
        avatar_color = "455a64"  # gray
        avatar_icon = "U"
    display_name = (user_obj.alias or user_obj.username or "U")[:2].upper()
    data["avatar"] = f"https://ui-avatars.com/api/?name={display_name}&background={avatar_color}&color=fff&size=128&bold=true&font-size=0.4"
    # Add city name
    if user_obj.default_city_id:
        from app.models.admin import City
        city = await City.filter(id=user_obj.default_city_id).first()
        data["default_city_name"] = city.name if city else ""
    else:
        data["default_city_name"] = ""
    data["role_names"] = [r.name for r in roles]
    return Success(data=data)


@router.get("/usermenu", summary="查看用户菜单", dependencies=[DependAuth])
async def get_user_menu():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()
    menus: list[Menu] = []
    if user_obj.is_superuser:
        menus = await Menu.all()
    else:
        role_objs: list[Role] = await user_obj.roles
        for role_obj in role_objs:
            menu = await role_obj.menus
            menus.extend(menu)
        menus = list(set(menus))
    parent_menus: list[Menu] = []
    for menu in menus:
        if menu.parent_id == 0:
            parent_menus.append(menu)
    res = []
    for parent_menu in parent_menus:
        parent_menu_dict = await parent_menu.to_dict()
        parent_menu_dict["children"] = []
        for menu in menus:
            if menu.parent_id == parent_menu.id:
                parent_menu_dict["children"].append(await menu.to_dict())
        res.append(parent_menu_dict)
    return Success(data=res)


@router.get("/userapi", summary="查看用户API", dependencies=[DependAuth])
async def get_user_api():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()
    if user_obj.is_superuser:
        api_objs: list[Api] = await Api.all()
        apis = [api.method.lower() + api.path for api in api_objs]
        return Success(data=apis)
    role_objs: list[Role] = await user_obj.roles
    apis = []
    for role_obj in role_objs:
        api_objs: list[Api] = await role_obj.apis
        apis.extend([api.method.lower() + api.path for api in api_objs])
    apis = list(set(apis))
    return Success(data=apis)


@router.post("/update_password", summary="修改密码", dependencies=[DependAuth])
async def update_user_password(req_in: UpdatePassword):
    user_id = CTX_USER_ID.get()
    user = await user_controller.get(user_id)
    verified = verify_password(req_in.old_password, user.password)
    if not verified:
        return Fail(msg="旧密码验证错误！")
    user.password = get_password_hash(req_in.new_password)
    await user.save()
    return Success(msg="修改成功")


@router.post("/update_profile", summary="更新个人信息", dependencies=[DependAuth])
async def update_profile(data: dict):
    """小程序端更新用户个人信息"""
    user_id = CTX_USER_ID.get()
    user = await user_controller.get(id=user_id)
    # Only update fields that exist on the User model
    if "alias" in data and data["alias"]:
        user.alias = data["alias"]
    if "phone" in data and data["phone"]:
        user.phone = data["phone"]
    # Store city info as default_city_id if a city name is provided
    if "city" in data and data["city"]:
        from app.models.admin import City
        city = await City.filter(name__contains=data["city"]).first()
        if city:
            user.default_city_id = city.id
    await user.save()
    return Success(msg="更新成功")


@router.post("/wx_login", summary="微信小程序登录")
async def wx_login(req_in: WxLoginSchema):
    """
    微信小程序登录：通过 wx.login 获取的 code 换取 openid，
    如果用户存在则返回 token，不存在则自动创建用户。
    """
    appid = settings.WECHAT_APPID
    secret = settings.WECHAT_SECRET

    if not appid or not secret:
        return Fail(msg="微信登录未配置，请联系管理员")

    # 调用微信 jscode2session 接口
    wx_url = (
        f"https://api.weixin.qq.com/sns/jscode2session"
        f"?appid={appid}&secret={secret}&js_code={req_in.code}&grant_type=authorization_code"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(wx_url, timeout=10)
    wx_data = resp.json()

    openid = wx_data.get("openid")
    if not openid:
        errcode = wx_data.get("errcode", "")
        errmsg = wx_data.get("errmsg", "未知错误")
        return Fail(msg=f"微信登录失败: {errcode} {errmsg}")

    session_key = wx_data.get("session_key", "")
    unionid = wx_data.get("unionid")

    # 查找或创建用户
    user = await User.filter(openid=openid).first()
    if not user:
        # 自动创建新用户
        username = f"wx_{openid[-8:]}"
        # 确保用户名不重复
        exists = await User.filter(username=username).first()
        if exists:
            username = f"wx_{openid[-12:]}"
        user = User(
            username=username,
            openid=openid,
            unionid=unionid,
            alias=req_in.nickname or "",
            avatar=req_in.avatar_url or "",
            email=f"{username}@wx.placeholder",
            is_active=True,
        )
        await user.save()
    else:
        # 更新用户信息（如果提供了）
        updated = False
        if req_in.nickname and not user.alias:
            user.alias = req_in.nickname
            updated = True
        if req_in.avatar_url and not user.avatar:
            user.avatar = req_in.avatar_url
            updated = True
        if unionid and not user.unionid:
            user.unionid = unionid
            updated = True
        if updated:
            await user.save()

    # 生成 JWT token
    await user_controller.update_last_login(user.id)
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + access_token_expires
    data = JWTOut(
        access_token=create_access_token(
            data=JWTPayload(
                user_id=user.id,
                username=user.username,
                is_superuser=user.is_superuser,
                exp=expire,
            )
        ),
        username=user.username,
    )
    return Success(data=data.model_dump())


@router.post("/wx_binduser", summary="绑定微信账号", dependencies=[DependAuth])
async def wx_bind_user(req_in: WxBindSchema):
    """
    已登录用户绑定微信 openid（管理员创建的账号后续绑定微信）
    """
    user_id = CTX_USER_ID.get()
    user = await user_controller.get(id=user_id)

    # 检查该 openid 是否已被其他用户绑定
    existing = await User.filter(openid=req_in.openid).first()
    if existing and existing.id != user.id:
        return Fail(msg="该微信号已被其他账号绑定")

    user.openid = req_in.openid
    await user.save()
    return Success(msg="绑定成功")


@router.get("/wx_bindstatus", summary="查询微信绑定状态", dependencies=[DependAuth])
async def wx_bind_status():
    """
    查询当前登录用户是否已绑定微信
    """
    user_id = CTX_USER_ID.get()
    user = await user_controller.get(id=user_id)
    return Success(data={"is_bound": bool(user.openid), "openid": user.openid or ""})
