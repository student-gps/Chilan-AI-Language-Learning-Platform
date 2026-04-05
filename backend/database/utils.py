import os
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from passlib.hash import pbkdf2_sha256
from config.env import get_env, get_env_int

# 新密码统一使用 pbkdf2_sha256，避免 Render / Python 3.14 环境下
# passlib+bcrypt 的兼容问题。旧用户如果库里存的是 bcrypt 哈希，仍做兼容验证。

SECRET_KEY = get_env("SECURITY_JWT_SECRET", "AUTH_JWT_SECRET", "JWT_SECRET", default="fallback_secret")
ALGORITHM = get_env("SECURITY_JWT_ALGORITHM", "AUTH_JWT_ALGORITHM", "ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = get_env_int(
    "SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES",
    "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    default=1440,
)

def get_password_hash(password: str):
    """哈希化存储密码"""
    return pbkdf2_sha256.hash(str(password))

def verify_password(plain_password: str, hashed_password: str):
    """校验明文密码与哈希值是否匹配"""
    plain_password = str(plain_password)
    hashed_password = str(hashed_password)

    if hashed_password.startswith("$pbkdf2-sha256$"):
        return pbkdf2_sha256.verify(plain_password, hashed_password)

    if hashed_password.startswith("$2a$") or hashed_password.startswith("$2b$") or hashed_password.startswith("$2y$"):
        # 兼容历史 bcrypt 哈希。历史上 bcrypt 实际只接受前 72 bytes。
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))

    return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建 JWT 访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
