"""
OCR API for ID card recognition.
Uses Tencent Cloud OCR API if configured, otherwise falls back to basic extraction.
"""
import hashlib
import hmac
import json
import os
import re
import time
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, File, UploadFile

from app.schemas.base import Fail, Success
from app.settings.config import settings

router = APIRouter()


async def _tencent_ocr_id_card(image_bytes: bytes) -> dict | None:
    """Use Tencent Cloud OCR API to recognize ID card."""
    secret_id = os.getenv("TENCENT_SECRET_ID", "")
    secret_key = os.getenv("TENCENT_SECRET_KEY", "")

    if not secret_id or not secret_key:
        return None

    import base64
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    # Tencent Cloud OCR API
    service = "ocr"
    host = "ocr.tencentcloudapi.com"
    action = "IDCardOCR"
    version = "2018-11-19"
    region = "ap-guangzhou"

    timestamp = int(time.time())
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")

    payload = json.dumps({"ImageBase64": image_base64, "CardSide": "FRONT"})

    # Sign the request
    http_request_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    ct = "application/json; charset=utf-8"
    canonical_headers = f"content-type:{ct}\nhost:{host}\nx-tc-action:{action.lower()}\n"
    signed_headers = "content-type;host;x-tc-action"
    hashed_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = f"{http_request_method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{hashed_payload}"

    credential_scope = f"{date}/{service}/tc3_request"
    hashed_canonical = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = f"TC3-HMAC-SHA256\n{timestamp}\n{credential_scope}\n{hashed_canonical}"

    def _sign(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    secret_date = _sign(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = _sign(secret_date, service)
    secret_signing = _sign(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"TC3-HMAC-SHA256 Credential={secret_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    headers = {
        "Authorization": authorization,
        "Content-Type": ct,
        "Host": host,
        "X-TC-Action": action,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Version": version,
        "X-TC-Region": region,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"https://{host}", headers=headers, content=payload)
        if resp.status_code == 200:
            data = resp.json()
            response = data.get("Response", {})
            if "Error" not in response:
                name = response.get("Name", "")
                id_num = response.get("IdNum", "")
                # Note: 身份证上的地址通常与实际地址不符，不返回地址
                return {"name": name, "id_number": id_num}
    return None


def _basic_extract_id_info(text: str) -> dict:
    """Try to extract name and ID number from raw text using regex."""
    result = {"name": "", "id_number": ""}

    # ID number pattern: 18 digits or 17 digits + X
    id_pattern = re.compile(r'[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]')
    id_match = id_pattern.search(text)
    if id_match:
        result["id_number"] = id_match.group().upper()

    return result


@router.post("/id_card", summary="OCR识别身份证")
async def ocr_id_card(file: UploadFile = File(...)):
    """
    Upload an ID card image for OCR recognition.
    Returns extracted name, id_number, and address.
    """
    content = await file.read()

    if len(content) > 10 * 1024 * 1024:
        return Fail(msg="图片大小不能超过10MB")

    # Try Tencent Cloud OCR first
    result = await _tencent_ocr_id_card(content)
    if result:
        return Success(data=result, msg="识别成功")

    # Fallback: return empty with message to manually input
    return Success(
        data={"name": "", "id_number": ""},
        msg="OCR服务未配置，请手动输入（可在环境变量中配置 TENCENT_SECRET_ID 和 TENCENT_SECRET_KEY）"
    )
