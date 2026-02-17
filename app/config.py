"""应用配置，优先从环境变量读取。"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用
    app_name: str = "AirComp能耗计算系统"
    secret_key: str = "change-me-in-production-use-env-SECRET_KEY"
    debug: bool = True

    # 数据库：默认 SQLite，便于本地直接运行；生产可改为 MySQL
    database_url: str = "sqlite:///./aircomp.db"

    # 邮件（可选，用于密码重置）
    mail_server: str = "smtp.qq.com"
    mail_port: int = 25
    mail_use_tls: bool = True
    mail_username: Optional[str] = None
    mail_password: Optional[str] = None
    mail_from: Optional[str] = None

    # 下载目录（相对项目根目录）
    download_dir: str = "app/download"

    @property
    def download_path(self) -> Path:
        return Path(__file__).resolve().parent / "download"


@lru_cache
def get_settings() -> Settings:
    return Settings()
