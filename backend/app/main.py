import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.api import api_router
from app.db.session import engine
from app.models.user import User, Post
from app.models.machine import MachineClient, MachineSupplier, MachineCompare
from app.models.analysis import AnalysisSession, AnalysisMessage
from app.db.session import Base

# 保证请求在终端有输出，便于排查“后台没有任何显示”
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger(__name__)
settings = get_settings()

# CORS：明确列出前端来源，确保 4xx/5xx 也能被浏览器正确识别（避免错误响应缺 CORS 头）
_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
if settings.FRONTEND_ORIGIN and settings.FRONTEND_ORIGIN not in _CORS_ORIGINS:
    _CORS_ORIGINS.append(settings.FRONTEND_ORIGIN)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """每个请求都在终端打印，便于确认请求是否到达后端"""
    async def dispatch(self, request, call_next):
        path = request.url.path or ""
        method = request.method or ""
        print(f"[AirComp] {method} {path}", flush=True)
        logger.info("%s %s", method, path)
        response = await call_next(request)
        print(f"[AirComp] {method} {path} -> {response.status_code}", flush=True)
        return response


app.add_middleware(RequestLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def add_cors_to_all_responses(request, call_next):
    """确保任意响应（含未捕获的 500）都带 CORS 头，避免浏览器先报 CORS"""
    response = await call_next(request)
    origin = request.headers.get("origin", "")
    if origin in _CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


def _cors_headers(origin: str):
    if origin in _CORS_ORIGINS:
        return {"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Credentials": "true"}
    return {}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """未捕获异常时返回带 CORS 头的响应，避免浏览器报 CORS 而掩盖真实错误"""
    from fastapi import HTTPException as FHTTPException
    origin = request.headers.get("origin", "")
    headers = _cors_headers(origin)
    if isinstance(exc, FHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=headers,
        )
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
        headers=headers,
    )

app.include_router(api_router, prefix="/api")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    print("[AirComp] 后端已启动，每个请求都会在终端打印 METHOD PATH", flush=True)


@app.get("/health")
def health():
    return {"status": "ok"}
