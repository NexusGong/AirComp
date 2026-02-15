"""
短信验证码服务（与 2Vision 一致：方法、参数、互亿无线 API）
"""
import logging
import random
import re
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# 短信验证码存储接口（与 2Vision 一致）
class SmsCodeStore:
    def store_code(
        self,
        phone: str,
        code: str,
        expire_time: datetime,
        last_send_time: float,
        verify_count: int = 0,
    ) -> None:
        raise NotImplementedError

    def get_code(self, phone: str) -> Optional[dict[str, Any]]:
        raise NotImplementedError

    def delete_code(self, phone: str) -> None:
        raise NotImplementedError

    def cleanup_expired(self) -> None:
        raise NotImplementedError


class InMemorySmsCodeStore(SmsCodeStore):
    def __init__(self) -> None:
        self._codes: dict[str, dict[str, Any]] = {}

    def store_code(
        self,
        phone: str,
        code: str,
        expire_time: datetime,
        last_send_time: float,
        verify_count: int = 0,
    ) -> None:
        self._codes[phone] = {
            "code": code,
            "expire_time": expire_time,
            "last_send_time": last_send_time,
            "verify_count": verify_count,
        }

    def get_code(self, phone: str) -> Optional[dict[str, Any]]:
        return self._codes.get(phone)

    def delete_code(self, phone: str) -> None:
        if phone in self._codes:
            del self._codes[phone]

    def cleanup_expired(self) -> None:
        now = datetime.utcnow()
        for phone in [p for p, info in self._codes.items() if now > info["expire_time"]]:
            del self._codes[phone]


_sms_code_store: SmsCodeStore = InMemorySmsCodeStore()

CODE_EXPIRE_MINUTES = 5
SEND_INTERVAL_SECONDS = 60


def _mask_phone(phone: str) -> str:
    if not phone or len(phone) < 7:
        return "****"
    return f"{phone[:3]}***{phone[-4:]}"


def generate_verification_code() -> str:
    return str(random.randint(100000, 999999))


def is_valid_phone(phone: str) -> bool:
    if not phone:
        return False
    phone = phone.strip().replace(" ", "").replace("-", "")
    return bool(re.match(r"^1\d{10}$", phone))


async def send_verification_code(phone: str) -> bool:
    """
    发送验证码（与 2Vision 一致）。
    未启用短信时仅内存存储并打日志；启用时调用互亿无线 API。
    """
    if not is_valid_phone(phone):
        return False

    existing = _sms_code_store.get_code(phone)
    if existing:
        last = existing.get("last_send_time", 0)
        if time.time() - last < SEND_INTERVAL_SECONDS:
            return False

    code = generate_verification_code()
    expire_time = datetime.utcnow() + timedelta(minutes=CODE_EXPIRE_MINUTES)
    _sms_code_store.store_code(phone, code, expire_time, time.time())

    settings = get_settings()
    if settings.SMS_ENABLED and settings.SMS_ACCOUNT and settings.SMS_PASSWORD:
        try:
            ok = await _send_sms_via_api(phone, code)
            if ok:
                logger.debug(f"[SMS] 验证码已发送到 {_mask_phone(phone)} (有效期{CODE_EXPIRE_MINUTES}分钟)")
            else:
                logger.warning(f"[SMS] API 发送失败，手机号={_mask_phone(phone)}")
            return True
        except Exception as e:
            logger.exception(f"[SMS] 发送异常: {e}, 手机号={_mask_phone(phone)}")
            return True
    else:
        logger.debug(f"[SMS] 模拟发送到 {_mask_phone(phone)}: {code} (有效期{CODE_EXPIRE_MINUTES}分钟)")
        print(f"[SMS] 验证码已发送到 {_mask_phone(phone)}：{code}（{CODE_EXPIRE_MINUTES} 分钟内有效）")
        return True


async def _send_sms_via_api(phone: str, code: str) -> bool:
    settings = get_settings()
    params = {
        "account": settings.SMS_ACCOUNT,
        "password": settings.SMS_PASSWORD,
        "mobile": phone,
        "content": code,
        "templateid": settings.SMS_TEMPLATE_ID,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                settings.SMS_API_URL,
                data=params,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if r.status_code != 200:
                logger.warning(f"[SMS] API 状态码 {r.status_code}")
                return False
            try:
                data = r.json()
                if data.get("code") == 2:
                    return True
                logger.warning(f"[SMS] 提交失败: {data.get('msg', '')} (code: {data.get('code')})")
                return False
            except Exception:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.text)
                code_el = root.find("code")
                if code_el is not None and int(code_el.text) == 2:
                    return True
                return False
    except httpx.TimeoutException:
        logger.warning("[SMS] 请求超时")
        return False
    except Exception as e:
        logger.exception(f"[SMS] 请求异常: {e}")
        return False


def verify_code(phone: str, code: str) -> bool:
    """验证验证码（与 2Vision 一致）"""
    if not is_valid_phone(phone) or not code:
        return False
    info = _sms_code_store.get_code(phone)
    if not info:
        return False
    if datetime.utcnow() > info["expire_time"]:
        _sms_code_store.delete_code(phone)
        return False
    verify_count = info.get("verify_count", 0)
    if verify_count >= 5:
        _sms_code_store.delete_code(phone)
        return False
    new_count = verify_count + 1
    _sms_code_store.store_code(
        phone, info["code"], info["expire_time"], info["last_send_time"], verify_count=new_count
    )
    if info["code"] == code:
        _sms_code_store.delete_code(phone)
        return True
    return False


def get_remaining_time(phone: str) -> int:
    """距离下次可发送的剩余秒数，0 表示可立即发送（与 2Vision 一致）"""
    info = _sms_code_store.get_code(phone)
    if not info:
        return 0
    elapsed = time.time() - info.get("last_send_time", 0)
    if elapsed >= SEND_INTERVAL_SECONDS:
        return 0
    return int(SEND_INTERVAL_SECONDS - elapsed)
