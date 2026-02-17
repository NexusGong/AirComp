"""豆包大模型 API 调用（智能录入：从文本/表格解析为能耗计算设备记录）"""
import json
import logging
import re
from datetime import date

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# 品牌枚举，用于校验与默认
BRANDS = ["英格索兰", "阿特拉斯", "寿力", "凯撒", "捷豹", "开山", "复盛", "其他"]

SYSTEM_PROMPT = """你是 AirComp 能耗计算系统设备信息抽取助手。用户会粘贴一段文本或表格（可能来自 Excel、文档），其中包含一条或多条设备信息。

**重要：你必须具备从多个列/多种表头中抽取并映射到所需标准字段的能力。** 表格可能有各种列名（例如：公司/单位名称/客户→公司名称，功率/额定功率(kW)/电机功率→额定功率，气量/排气量/额定气量(m³)→气量，压力/额定压力(MPa)→额定压力等）。请根据语义识别并映射到下面列出的标准字段，输出统一格式。

请从文本中识别出每一条设备记录，并严格按照以下 JSON 数组格式输出，不要输出任何其他说明文字，只输出一个 JSON 数组。

每条记录的标准字段（从用户的多列中识别并映射到这些键）：
- name: 公司名称（字符串；列名可能是：公司、公司名称、单位、客户等）
- no: 机器编号（整数；列名可能是：编号、机器编号、机号等）
- model: 机器型号（字符串；列名可能是：型号、机器型号、机型号等）
- run_time: 运行时间，单位小时（整数，缺省填 0）
- load_time: 加载时间，单位小时（整数，缺省填 0）
- ori_power: 额定功率，单位 kW（数字；列名可能是：功率、额定功率、额定功率(kW)、电机功率等）
- air: 额定气量，单位 m³（数字；列名可能是：气量、排气量、额定气量、额定气量(m³)等）
- brand: 品牌，必须是以下之一：英格索兰、阿特拉斯、寿力、凯撒、捷豹、开山、复盛、其他
- is_FC: 是否变频，true 或 false（列名可能是：是否变频、变频/工频、变频等，或从文本中推断）
- origin_pre: 额定压力，单位 MPa（数字，缺省 0.8；列名可能是：压力、额定压力、额定压力(MPa)等）
- actual_pre: 实际压力，单位 MPa（数字，缺省与额定相同）
- collect_time: 数据记录日期，格式 YYYY-MM-DD（缺省用今天；列名可能是：采集日期、数据记录日期、日期等）

若文本中只有一条设备信息，输出包含一个对象的数组；若有多条（如多行表格），输出多条。无法识别的数字字段用 0，无法识别的品牌用「其他」。"""


SYSTEM_PROMPT_SUPPLIER = """你是 AirComp 能耗计算系统供应商设备信息抽取助手。用户会粘贴一段文本或表格（可能来自 Excel、文档），其中包含一条或多条供应商设备信息。

**重要：你必须具备从多个列/多种表头中抽取并映射到所需标准字段的能力。** 表格可能有各种列名（例如：公司/供应商名称→公司名称，功率/额定功率(kW)→额定功率，气量/排气量→气量，比功率/比功率(kW/m³)→比功率等）。请根据语义识别并映射到下面列出的标准字段，输出统一格式。

请从文本中识别出每一条供应商设备记录，并严格按照以下 JSON 数组格式输出，不要输出任何其他说明文字，只输出一个 JSON 数组。

每条记录的标准字段（从用户的多列中识别并映射到这些键）：
- name: 供应商/公司名称（字符串；列名可能是：公司、供应商、公司名称等）
- no: 机器编号（整数；列名可能是：编号、机器编号、机号等）
- model: 机器型号（字符串；列名可能是：型号、机器型号等）
- ori_power: 额定功率，单位 kW（数字；列名可能是：功率、额定功率、额定功率(kW)等）
- air: 额定气量，单位 m³（数字；列名可能是：气量、排气量、额定气量等）
- energy_con: 比功率，单位 kW/m³（数字；列名可能是：比功率、比功率(kW/m³)、能效等）
- brand: 品牌，必须是以下之一：英格索兰、阿特拉斯、寿力、凯撒、捷豹、开山、复盛、其他
- is_FC: 是否变频，true 或 false（列名可能是：是否变频、变频/工频等，或从文本推断）
- origin_pre: 额定压力，单位 MPa（数字，缺省 0.8；列名可能是：压力、额定压力等）
- collect_time: 采集日期，格式 YYYY-MM-DD（缺省用今天；列名可能是：采集日期、日期等）

若文本中只有一条设备信息，输出包含一个对象的数组；若有多条（如多行表格），输出多条。无法识别的数字字段用 0，无法识别的品牌用「其他」。"""


def _normalize_record(raw: dict, default_date: str) -> dict:
    """将模型返回的单条记录规范为 API 所需格式"""
    def num(v, default=0):
        if v is None:
            return default
        if isinstance(v, (int, float)):
            return v
        s = str(v).strip().replace(",", "")
        m = re.search(r"-?\d+\.?\d*", s)
        return float(m.group()) if m else default

    def int_num(v, default=0):
        return int(round(num(v, default)))

    brand = (raw.get("brand") or "").strip()
    if brand not in BRANDS:
        brand = "其他"

    collect = (raw.get("collect_time") or "").strip()[:10]
    if not re.match(r"\d{4}-\d{2}-\d{2}", collect):
        collect = default_date

    return {
        "name": (raw.get("name") or "").strip() or "未填写",
        "no": int_num(raw.get("no"), 0),
        "model": (raw.get("model") or "").strip() or "未填写",
        "run_time": int_num(raw.get("run_time"), 0),
        "load_time": int_num(raw.get("load_time"), 0),
        "ori_power": num(raw.get("ori_power"), 0),
        "air": num(raw.get("air"), 0),
        "brand": brand,
        "is_FC": raw.get("is_FC") in (True, "true", "是", "变频", 1, "1"),
        "origin_pre": num(raw.get("origin_pre"), 0.8),
        "actual_pre": num(raw.get("actual_pre"), num(raw.get("origin_pre"), 0.8)),
        "collect_time": collect,
    }


async def parse_equipment_text(text: str) -> list[dict]:
    """
    调用豆包 API，将用户粘贴的文本或表格内容解析为多条设备记录。
    返回 list[dict]，每条符合 MachineClientCreate 字段。
    """
    settings = get_settings()
    if not (settings.DOUBAO_API_KEY or "").strip():
        logger.warning("智能解析: DOUBAO_API_KEY 未配置")
        raise ValueError("未配置豆包 API Key，请在后台 .env 中设置 DOUBAO_API_KEY")
    if not text or not text.strip():
        return []

    url = (settings.DOUBAO_API_URL or "").strip()
    if not url:
        raise ValueError("未配置豆包 API 地址 DOUBAO_API_URL")

    default_date = date.today().isoformat()
    payload = {
        "model": settings.DOUBAO_MODEL or "doubao-seed-1-6-vision-250815",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "请从以下文本中抽取所有设备记录，只输出 JSON 数组：\n\n" + text.strip()},
        ],
        "stream": False,
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {settings.DOUBAO_API_KEY.strip()}",
        "Content-Type": "application/json",
    }

    logger.info("智能解析(客户): 请求豆包 API, url=%s, text_len=%d", url, len(text))
    timeout = httpx.Timeout(10.0, read=60.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException as e:
        logger.exception("智能解析: 豆包 API 超时")
        raise ValueError("豆包 API 请求超时，请稍后重试") from e
    except Exception as e:
        logger.exception("智能解析: 豆包 API 调用失败: %s", e)
        raise ValueError(f"豆包 API 调用失败: {e}") from e

    content = ""
    for choice in (data.get("choices") or []):
        msg = choice.get("message") or {}
        content = (msg.get("content") or "").strip()
        if content:
            break

    if not content:
        return []

    # 抽取 JSON 数组（可能被 markdown 包裹）
    json_match = re.search(r"\[[\s\S]*\]", content)
    if not json_match:
        return []

    try:
        raw_list = json.loads(json_match.group())
    except json.JSONDecodeError:
        return []

    if not isinstance(raw_list, list):
        return []

    return [_normalize_record(item, default_date) for item in raw_list if isinstance(item, dict)]


def _normalize_record_supplier(raw: dict, default_date: str) -> dict:
    """将模型返回的单条供应商记录规范为 API 所需格式"""
    def num(v, default=0):
        if v is None:
            return default
        if isinstance(v, (int, float)):
            return v
        s = str(v).strip().replace(",", "")
        m = re.search(r"-?\d+\.?\d*", s)
        return float(m.group()) if m else default

    def int_num(v, default=0):
        return int(round(num(v, default)))

    brand = (raw.get("brand") or "").strip()
    if brand not in BRANDS:
        brand = "其他"

    collect = (raw.get("collect_time") or "").strip()[:10]
    if not re.match(r"\d{4}-\d{2}-\d{2}", collect):
        collect = default_date

    return {
        "name": (raw.get("name") or "").strip() or "未填写",
        "no": int_num(raw.get("no"), 0),
        "model": (raw.get("model") or "").strip() or "未填写",
        "ori_power": num(raw.get("ori_power"), 0),
        "air": num(raw.get("air"), 0),
        "brand": brand,
        "is_FC": raw.get("is_FC") in (True, "true", "是", "变频", 1, "1"),
        "origin_pre": num(raw.get("origin_pre"), 0.8),
        "energy_con": num(raw.get("energy_con"), 0),
        "collect_time": collect,
    }


async def parse_equipment_text_supplier(text: str) -> list[dict]:
    """
    调用豆包 API，将用户粘贴的文本或表格内容解析为多条供应商设备记录。
    返回 list[dict]，每条符合 MachineSupplierCreate 字段。
    """
    settings = get_settings()
    if not (settings.DOUBAO_API_KEY or "").strip():
        logger.warning("智能解析(供应商): DOUBAO_API_KEY 未配置")
        raise ValueError("未配置豆包 API Key，请在后台 .env 中设置 DOUBAO_API_KEY")
    if not text or not text.strip():
        return []

    url = (settings.DOUBAO_API_URL or "").strip()
    if not url:
        raise ValueError("未配置豆包 API 地址 DOUBAO_API_URL")

    default_date = date.today().isoformat()
    payload = {
        "model": settings.DOUBAO_MODEL or "doubao-seed-1-6-vision-250815",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_SUPPLIER},
            {"role": "user", "content": "请从以下文本中抽取所有供应商设备记录，只输出 JSON 数组：\n\n" + text.strip()},
        ],
        "stream": False,
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {settings.DOUBAO_API_KEY.strip()}",
        "Content-Type": "application/json",
    }

    logger.info("智能解析(供应商): 请求豆包 API, url=%s, text_len=%d", url, len(text))
    timeout = httpx.Timeout(10.0, read=60.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException as e:
        logger.exception("智能解析(供应商): 豆包 API 超时")
        raise ValueError("豆包 API 请求超时，请稍后重试") from e
    except Exception as e:
        logger.exception("智能解析(供应商): 豆包 API 调用失败: %s", e)
        raise ValueError(f"豆包 API 调用失败: {e}") from e

    content = ""
    for choice in (data.get("choices") or []):
        msg = choice.get("message") or {}
        content = (msg.get("content") or "").strip()
        if content:
            break

    if not content:
        return []

    json_match = re.search(r"\[[\s\S]*\]", content)
    if not json_match:
        return []

    try:
        raw_list = json.loads(json_match.group())
    except json.JSONDecodeError:
        return []

    if not isinstance(raw_list, list):
        return []

    return [_normalize_record_supplier(item, default_date) for item in raw_list if isinstance(item, dict)]


async def chat_completion(messages: list[dict], temperature: float = 0.3) -> str:
    """通用对话补全，返回助手回复的 content 文本。"""
    settings = get_settings()
    if not (settings.DOUBAO_API_KEY or "").strip():
        raise ValueError("未配置豆包 API Key")
    url = (settings.DOUBAO_API_URL or "").strip()
    if not url:
        raise ValueError("未配置豆包 API 地址 DOUBAO_API_URL")
    payload = {
        "model": settings.DOUBAO_MODEL or "doubao-seed-1-6-vision-250815",
        "messages": messages,
        "stream": False,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {settings.DOUBAO_API_KEY.strip()}",
        "Content-Type": "application/json",
    }
    timeout = httpx.Timeout(15.0, read=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    content = ""
    for choice in (data.get("choices") or []):
        msg = choice.get("message") or {}
        content = (msg.get("content") or "").strip()
        if content:
            break
    return content or ""


async def chat_completion_stream(messages: list[dict], temperature: float = 0.3):
    """
    流式对话补全，按 SSE 解析豆包返回，逐块 yield 文本内容。
    与 OpenAI Chat Completions 流式格式兼容：data: {"choices":[{"delta":{"content":"..."}}]}
    """
    settings = get_settings()
    if not (settings.DOUBAO_API_KEY or "").strip():
        raise ValueError("未配置豆包 API Key")
    url = (settings.DOUBAO_API_URL or "").strip()
    if not url:
        raise ValueError("未配置豆包 API 地址 DOUBAO_API_URL")
    payload = {
        "model": settings.DOUBAO_MODEL or "doubao-seed-1-6-vision-250815",
        "messages": messages,
        "stream": True,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {settings.DOUBAO_API_KEY.strip()}",
        "Content-Type": "application/json",
    }
    timeout = httpx.Timeout(15.0, read=120.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]" or data_str == "[done]":
                    break
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                for choice in (data.get("choices") or []):
                    delta = choice.get("delta") or {}
                    content = delta.get("content")
                    if content and isinstance(content, str):
                        yield content
