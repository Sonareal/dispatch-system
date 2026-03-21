import time
import logging

import httpx

from app.settings import settings

logger = logging.getLogger(__name__)

# 缓存 access_token
_access_token_cache = {
    "token": "",
    "expires_at": 0,
}


async def get_access_token() -> str:
    """
    获取微信服务端 access_token，带缓存（提前 5 分钟过期）。
    返回空字符串表示未配置或获取失败。
    """
    appid = settings.WECHAT_APPID
    secret = settings.WECHAT_SECRET

    if not appid or not secret:
        return ""

    now = time.time()
    if _access_token_cache["token"] and _access_token_cache["expires_at"] > now:
        return _access_token_cache["token"]

    url = (
        f"https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential&appid={appid}&secret={secret}"
    )
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
        data = resp.json()
        token = data.get("access_token", "")
        expires_in = data.get("expires_in", 7200)
        if token:
            _access_token_cache["token"] = token
            # 提前 5 分钟刷新
            _access_token_cache["expires_at"] = now + expires_in - 300
        return token
    except Exception as e:
        logger.error(f"获取微信 access_token 失败: {e}")
        return ""


async def send_subscribe_message(
    openid: str,
    template_id: str,
    data: dict,
    page: str = "",
) -> bool:
    """
    发送微信订阅消息。

    参数:
        openid: 接收者的 openid
        template_id: 订阅消息模板 ID
        data: 模板数据，格式如 {"key1": {"value": "xxx"}, ...}
        page: 点击消息跳转的小程序页面（可选）

    返回:
        是否发送成功
    """
    if not openid or not template_id:
        return False

    access_token = await get_access_token()
    if not access_token:
        logger.warning("未获取到 access_token，跳过发送订阅消息")
        return False

    url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}"
    payload = {
        "touser": openid,
        "template_id": template_id,
        "data": data,
    }
    if page:
        payload["page"] = page

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10)
        result = resp.json()
        errcode = result.get("errcode", 0)
        if errcode != 0:
            errmsg = result.get("errmsg", "")
            logger.warning(f"发送订阅消息失败: errcode={errcode}, errmsg={errmsg}")
            return False
        return True
    except Exception as e:
        logger.error(f"发送订阅消息异常: {e}")
        return False
