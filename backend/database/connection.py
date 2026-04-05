import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path
from config.env import get_env

# 自动定位项目根目录下的 .env 文件
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DB_URL = get_env("APP_DATABASE_URL", "DB_DATABASE_URL", "DATABASE_URL")

def get_connection():
    """获取标准的 PostgreSQL 连接"""
    if not DB_URL:
        raise ValueError("未在 .env 中找到 APP_DATABASE_URL / DB_DATABASE_URL / DATABASE_URL")
    return psycopg2.connect(DB_URL)
