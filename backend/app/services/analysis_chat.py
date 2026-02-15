"""分析页对话：意图识别、设备解析落库、能耗计算意图解析"""
import json
import logging
import re
from datetime import date

from sqlalchemy.orm import Session

from app.models import User, MachineClient, MachineSupplier
from app.services.doubao import (
    chat_completion,
    chat_completion_stream,
    parse_equipment_text,
    parse_equipment_text_supplier,
)

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """你是空压机能效分析助手。用户在与您对话中可能：
1. 粘贴或上传客户设备表格/文本（公司、型号、功率、气量、运行时间等）→ 意图为 upload_client
2. 粘贴或上传供应商设备表格/文本（供应商、型号、比功率等）→ 意图为 upload_supplier
3. 询问「接下来做什么」「怎么算」等 → 意图为 general，并引导：可进行能耗计算，请告知要计算哪家客户的哪些设备（如「计算测试公司A的1号2号机」）
4. 明确要求计算某家客户的节能量，如「计算测试公司A的1号2号机的节能量」「算一下测试公司B的全部设备」→ 意图为 run_energy_calculation，并从中提取公司名与机器编号。

请根据用户当前消息和上下文，只输出一个 JSON 对象，不要其他文字。格式：
{
  "intent": "upload_client" | "upload_supplier" | "run_energy_calculation" | "general",
  "reply": "给用户的自然语言回复（中文）",
  "company_name": "仅当 intent 为 run_energy_calculation 时填写，从用户话中提取的公司名",
  "client_nos": [1, 2]
}

规则：
- client_nos 仅当 intent 为 run_energy_calculation 时存在；若用户说「全部设备」或未指定编号则输出空数组 []；若指定了编号则输出整数数组如 [1, 2]。
- 若消息看起来像表格或带表头多行数据，且包含公司/客户、型号、功率、气量、运行时间等，intent 设为 upload_client；若包含供应商、比功率等，设为 upload_supplier。
- 若无法判断表格类型，优先 upload_client。
- reply 要简短友好；若为 general 可顺带说明当前已有客户列表（若下方提供了 context_clients）并引导下一步。"""

ANALYSIS_INTENT_ONLY_PROMPT = """你是空压机能效分析助手。仅根据用户当前消息和上下文，输出一个 JSON 对象，只包含以下键，不要 reply。
- intent: "upload_client" | "upload_supplier" | "run_energy_calculation" | "general"
- company_name: 仅当 intent 为 run_energy_calculation 时填写公司名
- client_nos: 仅当 intent 为 run_energy_calculation 时填写，整数数组，未指定则 []

规则：若用户明确要求「计算…节能量」「算…能耗」等且能提取公司名，优先 intent 为 run_energy_calculation（即使消息中含表格）；纯表格/设备数据且未要求计算时 intent 为 upload_client 或 upload_supplier；询问下一步为 general。只输出 JSON，不要其他文字。"""

REPLY_GEN_PROMPT = """你是空压机能效分析助手。根据用户消息和当前上下文，用一两句话简短回复（中文），引导下一步或回答问题。不要输出 JSON，只输出回复正文。"""


def _extract_json(content: str) -> dict | None:
    """从回复中抽取 JSON 对象。"""
    content = (content or "").strip()
    # 尝试 markdown 代码块
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
    if m:
        raw = m.group(1).strip()
    else:
        raw = content
    # 找 { ... }
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        return None


def _batch_create_clients(db: Session, user: User, items: list[dict]) -> tuple[int, int]:
    """批量创建客户设备，返回 (created, skipped)。"""
    created = skipped = 0
    for data in items:
        existing = db.query(MachineClient).filter(
            MachineClient.name == data["name"],
            MachineClient.no == data["no"],
        ).first()
        if existing:
            skipped += 1
            continue
        collect = data.get("collect_time") or date.today().isoformat()
        if isinstance(collect, str):
            try:
                collect = date.fromisoformat(collect[:10])
            except Exception:
                collect = date.today()
        row = MachineClient(
            user_id=user.id,
            name=data["name"],
            no=data["no"],
            model=data["model"],
            run_time=data.get("run_time", 0),
            load_time=data.get("load_time", 0),
            ori_power=data.get("ori_power", 0),
            air=data.get("air", 0),
            brand=data.get("brand", "其他"),
            is_FC=1 if data.get("is_FC") else 0,
            origin_pre=data.get("origin_pre", 0.8),
            actual_pre=data.get("actual_pre", data.get("origin_pre", 0.8)),
            collect_time=collect,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        created += 1
    return created, skipped


def _batch_create_suppliers(db: Session, user: User, items: list[dict]) -> tuple[int, int]:
    """批量创建供应商设备，返回 (created, skipped)。"""
    created = skipped = 0
    for data in items:
        existing = db.query(MachineSupplier).filter(
            MachineSupplier.name == data["name"],
            MachineSupplier.model == data["model"],
        ).first()
        if existing:
            skipped += 1
            continue
        collect = data.get("collect_time") or date.today().isoformat()
        if isinstance(collect, str):
            try:
                collect = date.fromisoformat(collect[:10])
            except Exception:
                collect = date.today()
        energy_con = float(data.get("energy_con") or 0)
        energy_con_min = energy_con / 60
        row = MachineSupplier(
            user_id=user.id,
            name=data["name"],
            no=data.get("no", 0),
            model=data["model"],
            ori_power=data.get("ori_power", 0),
            air=data.get("air", 0),
            brand=data.get("brand", "其他"),
            is_FC=1 if data.get("is_FC") else 0,
            origin_pre=data.get("origin_pre", 0.8),
            energy_con=energy_con,
            energy_con_min=energy_con_min,
            collect_time=collect,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        created += 1
    return created, skipped


async def handle_analysis_chat(
    message: str,
    history: list[dict],
    attachments: list[dict],
    db: Session,
    current_user: User,
    context_clients: list[str] | None = None,
) -> dict:
    """
    处理分析页一条用户消息：意图识别、设备解析落库、能耗计算参数解析。
    返回: reply, intent, created_clients?, created_suppliers?, company_name?, client_nos?, client_list?
    """
    full_text = (message or "").strip()
    for a in attachments or []:
        if a.get("type") in ("text", "file") and a.get("content"):
            full_text += "\n" + (a["content"] or "").strip()
    full_text = full_text.strip()

    # 构建对话消息
    msgs = [{"role": "system", "content": ANALYSIS_SYSTEM_PROMPT}]
    if context_clients:
        msgs[0]["content"] += "\n\n当前用户已有客户公司名称列表：" + "、".join(context_clients)
    for h in (history or [])[-10:]:
        role = h.get("role", "user")
        content = (h.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": full_text or "（无内容）"})

    content = await chat_completion(msgs)
    parsed = _extract_json(content)
    intent = "general"
    reply = "请发送设备表格或说明您要进行的操作。"
    company_name = None
    client_nos = None
    client_list = None
    created_clients = None
    created_suppliers = None

    if parsed:
        intent = parsed.get("intent") or "general"
        reply = (parsed.get("reply") or reply).strip()
        company_name = parsed.get("company_name") or None
        if company_name and isinstance(company_name, str):
            company_name = company_name.strip() or None
        client_nos = parsed.get("client_nos")
        if not isinstance(client_nos, list):
            client_nos = None

    # 执行意图对应动作
    if intent == "upload_client" and full_text:
        try:
            records = await parse_equipment_text(full_text)
            if records:
                created, skipped = _batch_create_clients(db, current_user, records)
                created_clients = {"created": created, "skipped": skipped, "total": len(records)}
                reply = f"已录入 {created} 条客户设备" + (f"，{skipped} 条已存在已跳过。" if skipped else "。") + " 接下来可以进行能耗计算，请告诉我您要计算哪家客户的设备节能量（可指定公司名和机器编号，如「计算测试公司A的1号2号机」）。"
            else:
                reply = "未能从内容中识别到设备记录，请确认是否为客户设备表格（含公司、型号、功率、气量等）。"
        except ValueError as e:
            reply = str(e)
        except Exception as e:
            logger.exception("分析页上传客户设备失败: %s", e)
            reply = "解析或保存失败，请稍后重试。"

    elif intent == "upload_supplier" and full_text:
        try:
            records = await parse_equipment_text_supplier(full_text)
            if records:
                created, skipped = _batch_create_suppliers(db, current_user, records)
                created_suppliers = {"created": created, "skipped": skipped, "total": len(records)}
                reply = f"已录入 {created} 条供应商设备" + (f"，{skipped} 条已存在已跳过。" if skipped else "。")
            else:
                reply = "未能从内容中识别到供应商设备记录，请确认是否包含供应商、型号、比功率等。"
        except ValueError as e:
            reply = str(e)
        except Exception as e:
            logger.exception("分析页上传供应商设备失败: %s", e)
            reply = "解析或保存失败，请稍后重试。"

    elif intent == "run_energy_calculation" and company_name:
        # 查询客户机列表
        q = db.query(MachineClient).filter(MachineClient.name == company_name)
        if current_user.id != 999:
            q = q.filter(MachineClient.user_id == current_user.id)
        if client_nos:
            q = q.filter(MachineClient.no.in_(client_nos))
        clients = q.order_by(MachineClient.no).all()
        if clients:
            client_list = [
                {"no": c.no, "model": c.model, "brand": c.brand, "name": c.name}
                for c in clients
            ]
            reply = f"将计算：{company_name}，共 {len(client_list)} 台设备（编号：{[c.no for c in clients]}）。请先点击「确认选型」获取方案，再点击「确认参数」进行节能计算与报告生成。"
        else:
            reply = f"未找到客户「{company_name}」" + (f" 编号 {client_nos} 的设备。" if client_nos else " 下的设备，请先录入。")

    out = {
        "reply": reply,
        "intent": intent,
    }
    if created_clients is not None:
        out["created_clients"] = created_clients
    if created_suppliers is not None:
        out["created_suppliers"] = created_suppliers
    if company_name is not None:
        out["company_name"] = company_name
    if client_nos is not None:
        out["client_nos"] = client_nos
    if client_list is not None:
        out["client_list"] = client_list
    return out


async def _chunk_string(s: str, size: int = 2):
    """把字符串按 size 字符一块 yield，用于后端向 SSE 推送。"""
    s = s or ""
    for i in range(0, len(s), size):
        yield s[i : i + size]


async def handle_analysis_chat_stream(
    message: str,
    history: list[dict],
    attachments: list[dict],
    db: Session,
    current_user: User,
    context_clients: list[str] | None = None,
):
    """
    与 handle_analysis_chat 逻辑一致，但以流式 yield (type, data)。
    type 为 "content" 时 data 为文本块；为 "done" 时 data 为 JSON 字符串（metadata）。
    """
    full_text = (message or "").strip()
    for a in attachments or []:
        if a.get("type") in ("text", "file") and a.get("content"):
            full_text += "\n" + (a["content"] or "").strip()
    full_text = full_text.strip()

    msgs_intent = [{"role": "system", "content": ANALYSIS_INTENT_ONLY_PROMPT}]
    if context_clients:
        msgs_intent[0]["content"] += "\n\n当前用户已有客户公司名称列表：" + "、".join(context_clients)
    for h in (history or [])[-10:]:
        role = h.get("role", "user")
        content = (h.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            msgs_intent.append({"role": role, "content": content})
    msgs_intent.append({"role": "user", "content": full_text or "（无内容）"})

    content = await chat_completion(msgs_intent)
    parsed = _extract_json(content)
    intent = "general"
    company_name = None
    client_nos = None
    client_list = None
    created_clients = None
    created_suppliers = None
    reply = None

    if parsed:
        intent = parsed.get("intent") or "general"
        company_name = parsed.get("company_name") or None
        if company_name and isinstance(company_name, str):
            company_name = company_name.strip() or None
        client_nos = parsed.get("client_nos")
        if not isinstance(client_nos, list):
            client_nos = None

    if intent == "upload_client" and full_text:
        try:
            records = await parse_equipment_text(full_text)
            if records:
                created, skipped = _batch_create_clients(db, current_user, records)
                created_clients = {"created": created, "skipped": skipped, "total": len(records)}
                reply = f"已录入 {created} 条客户设备" + (f"，{skipped} 条已存在已跳过。" if skipped else "。") + " 接下来可以进行能耗计算，请告诉我您要计算哪家客户的设备节能量（可指定公司名和机器编号，如「计算测试公司A的1号2号机」）。"
            else:
                reply = "未能从内容中识别到设备记录，请确认是否为客户设备表格（含公司、型号、功率、气量等）。"
        except ValueError as e:
            reply = str(e)
        except Exception as e:
            logger.exception("分析页上传客户设备失败: %s", e)
            reply = "解析或保存失败，请稍后重试。"

    elif intent == "upload_supplier" and full_text:
        try:
            records = await parse_equipment_text_supplier(full_text)
            if records:
                created, skipped = _batch_create_suppliers(db, current_user, records)
                created_suppliers = {"created": created, "skipped": skipped, "total": len(records)}
                reply = f"已录入 {created} 条供应商设备" + (f"，{skipped} 条已存在已跳过。" if skipped else "。")
            else:
                reply = "未能从内容中识别到供应商设备记录，请确认是否包含供应商、型号、比功率等。"
        except ValueError as e:
            reply = str(e)
        except Exception as e:
            logger.exception("分析页上传供应商设备失败: %s", e)
            reply = "解析或保存失败，请稍后重试。"

    elif intent == "run_energy_calculation" and company_name:
        q = db.query(MachineClient).filter(MachineClient.name == company_name)
        if current_user.id != 999:
            q = q.filter(MachineClient.user_id == current_user.id)
        if client_nos:
            q = q.filter(MachineClient.no.in_(client_nos))
        clients = q.order_by(MachineClient.no).all()
        if clients:
            client_list = [
                {"no": c.no, "model": c.model, "brand": c.brand, "name": c.name}
                for c in clients
            ]
            reply = f"将计算：{company_name}，共 {len(client_list)} 台设备（编号：{[c.no for c in clients]}）。请先点击「确认选型」获取方案，再点击「确认参数」进行节能计算与报告生成。"
        else:
            reply = f"未找到客户「{company_name}」" + (f" 编号 {client_nos} 的设备。" if client_nos else " 下的设备，请先录入。")

    if reply is not None:
        async for chunk in _chunk_string(reply, 2):
            yield "content", chunk
    else:
        reply_msgs = [{"role": "system", "content": REPLY_GEN_PROMPT}]
        if context_clients:
            reply_msgs[0]["content"] += "\n\n当前用户已有客户列表：" + "、".join(context_clients)
        reply_msgs.append({"role": "user", "content": full_text or "（无内容）"})
        async for chunk in chat_completion_stream(reply_msgs):
            yield "content", chunk

    metadata = {
        "intent": intent,
        "company_name": company_name,
        "client_nos": client_nos,
        "client_list": client_list,
        "created_clients": created_clients,
        "created_suppliers": created_suppliers,
    }
    yield "done", json.dumps(metadata, ensure_ascii=False)
