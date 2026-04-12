import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path
from config.env import get_env

# 自动定位项目根目录下的 .env 文件
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

def _resolve_db_url() -> str:
    mode = (get_env("DB_MODE") or "cloud").strip().lower()
    if mode == "local":
        url = get_env("APP_DATABASE_URL_LOCAL")
        if not url:
            raise ValueError("DB_MODE=local 但未在 .env 中找到 APP_DATABASE_URL_LOCAL")
        return url
    url = get_env("APP_DATABASE_URL")
    if not url:
        raise ValueError("DB_MODE=cloud 但未在 .env 中找到 APP_DATABASE_URL")
    return url

DB_URL = _resolve_db_url()

def get_connection():
    """获取标准的 PostgreSQL 连接（由 DB_MODE 决定使用云端或本地）"""
    return psycopg2.connect(DB_URL)
