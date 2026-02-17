"""应用配置 - 使用 pydantic-settings 管理环境变量，.env 与 2Vision 变量名一致可共用"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os

# 固定从 backend 目录加载 .env，与运行时的 cwd 无关
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    # 应用
    APP_NAME: str = "AirComp能耗计算系统"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    DEBUG: bool = True

    # 数据库（SQLite）
    SQLITE_PATH: str = "aircomp.db"

    # JWT（登录保持 7 天）
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天，与前端「登录状态保持 7 天」一致

    # 前端地址 (CORS)
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # 短信服务（互亿无线，与 2Vision 一致；.env 可直接复用 2Vision 的短信配置）
    SMS_ENABLED: bool = False
    SMS_ACCOUNT: str = ""
    SMS_PASSWORD: str = ""
    SMS_TEMPLATE_ID: str = "1"
    SMS_API_URL: str = "https://api.ihuyi.com/sms/Submit.json"
    SMS_BALANCE_THRESHOLD: float | None = None  # 余额低于此值告警，不设则不检查

    # 豆包大模型（智能录入）
    DOUBAO_API_KEY: str = ""
    DOUBAO_API_URL: str = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    DOUBAO_MODEL: str = "doubao-seed-1-6-vision-250815"

    @property
    def DATABASE_URI(self) -> str:
        """SQLite 数据库路径（相对于 backend 目录）"""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(base_dir, self.SQLITE_PATH)
        return f"sqlite:///{path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
