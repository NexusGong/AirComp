"""分析页对话 API"""
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import User, MachineClient, AnalysisSession, AnalysisMessage
from app.services.analysis_chat import handle_analysis_chat, handle_analysis_chat_stream

router = APIRouter(prefix="/analysis", tags=["analysis"])

ADMIN_ID = 999


class ChatMessage(BaseModel):
    role: str
    content: str


class Attachment(BaseModel):
    type: str  # "text" | "file"
    content: str


class AnalysisChatRequest(BaseModel):
    message: str
    session_id: int | None = None
    history: list[ChatMessage] | None = None
    attachments: list[Attachment] | None = None


def _title_from_content(content: str, max_len: int = 28) -> str:
    first = (content or "").strip().split("\n")[0] or (content or "").strip()
    return (first[:max_len] or "新建对话").strip()


@router.post("/chat")
async def analysis_chat(
    body: AnalysisChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分析页对话：支持意图识别、设备表格解析落库、能耗计算意图解析。可选 session_id 持久化消息。"""
    history = None
    if body.history:
        history = [{"role": m.role, "content": m.content} for m in body.history]
    attachments = None
    if body.attachments:
        attachments = [{"type": a.type, "content": a.content} for a in body.attachments]

    # 当前用户客户列表，供模型引导用
    q = db.query(MachineClient.name).filter(MachineClient.name.isnot(None)).distinct()
    if current_user.id != ADMIN_ID:
        q = q.filter(MachineClient.user_id == current_user.id)
    context_clients = [r[0] for r in q.all() if r[0]]

    try:
        result = await handle_analysis_chat(
            message=body.message,
            history=history,
            attachments=attachments,
            db=db,
            current_user=current_user,
            context_clients=context_clients or None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 持久化到 AnalysisSession / AnalysisMessage（可选）
    session_id = body.session_id
    if session_id is not None:
        session = db.query(AnalysisSession).filter(
            AnalysisSession.id == session_id,
            AnalysisSession.user_id == current_user.id,
        ).first()
        if not session:
            session_id = None
    if session_id is None:
        session = AnalysisSession(
            user_id=current_user.id,
            title=_title_from_content(body.message),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id

    # 保存本轮 user + assistant 消息
    db.add(AnalysisMessage(session_id=session_id, role="user", content=body.message))
    db.add(AnalysisMessage(session_id=session_id, role="assistant", content=result.get("reply", "")))
    db.commit()

    result["session_id"] = session_id
    return result


def _sse_line(event: str, data: str) -> str:
    """生成一条 SSE：event + data；data 内换行按 SSE 规范用多行 data 表示。"""
    lines = (data or "").split("\n")
    out = f"event: {event}\n"
    for line in lines:
        out += f"data: {line}\n"
    out += "\n"
    return out


@router.post("/chat/stream")
async def analysis_chat_stream(
    body: AnalysisChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """流式对话：先推 content 事件（文本块），最后推 done 事件（含 intent、session_id 等）。"""
    history = None
    if body.history:
        history = [{"role": m.role, "content": m.content} for m in body.history]
    attachments = None
    if body.attachments:
        attachments = [{"type": a.type, "content": a.content} for a in body.attachments]

    q = db.query(MachineClient.name).filter(MachineClient.name.isnot(None)).distinct()
    if current_user.id != ADMIN_ID:
        q = q.filter(MachineClient.user_id == current_user.id)
    context_clients = [r[0] for r in q.all() if r[0]]

    async def generate():
        reply_acc = []
        metadata = None
        try:
            async for typ, data in handle_analysis_chat_stream(
                message=body.message,
                history=history,
                attachments=attachments,
                db=db,
                current_user=current_user,
                context_clients=context_clients or None,
            ):
                if typ == "content":
                    reply_acc.append(data)
                    yield _sse_line("content", data)
                elif typ == "done":
                    metadata = json.loads(data)
                    break
        except Exception as e:
            yield _sse_line("error", json.dumps({"detail": str(e)}, ensure_ascii=False))
            return

        full_reply = "".join(reply_acc)
        session_id = body.session_id
        if session_id is not None:
            session = db.query(AnalysisSession).filter(
                AnalysisSession.id == session_id,
                AnalysisSession.user_id == current_user.id,
            ).first()
            if not session:
                session_id = None
        if session_id is None:
            session = AnalysisSession(
                user_id=current_user.id,
                title=_title_from_content(body.message),
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            session_id = session.id

        db.add(AnalysisMessage(session_id=session_id, role="user", content=body.message))
        db.add(AnalysisMessage(session_id=session_id, role="assistant", content=full_reply))
        db.commit()

        metadata["session_id"] = session_id
        metadata["reply"] = full_reply
        yield _sse_line("done", json.dumps(metadata, ensure_ascii=False))

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
