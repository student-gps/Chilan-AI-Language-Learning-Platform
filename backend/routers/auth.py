import os, re, random, httpx, jwt, smtplib, traceback
from email.mime.text import MIMEText
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from jwt import PyJWKClient
from psycopg2.extras import RealDictCursor
from database.connection import get_connection
from database.utils import get_password_hash, verify_password, create_access_token
from config.env import get_env, get_env_bool, get_env_int

router = APIRouter(prefix="/auth", tags=["Authentication"])

# --- 模型定义 ---
class SignupReq(BaseModel):
    email: EmailStr
    password: str
    lang: str = "zh"

class VerifyReq(BaseModel):
    email: EmailStr
    code: str

class LoginReq(BaseModel):
    email: EmailStr
    password: str

class ForgotReq(BaseModel):
    email: EmailStr

class ResetReq(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class GoogleAuthReq(BaseModel):
    access_token: str

class AppleAuthReq(BaseModel):
    token: str
    firstName: str = None
    lastName: str = None

class UpdateProfileReq(BaseModel):
    username: str

class ChangePasswordReq(BaseModel):
    current_password: str
    new_password: str

class DeleteAccountReq(BaseModel):
    confirm_text: str
    current_password: str | None = None

def get_db():
    conn = get_connection()
    try: yield conn
    finally: conn.close()

def resolve_login_provider(password_hash: str) -> str:
    if password_hash == "GOOGLE_USER":
        return "google"
    if password_hash == "APPLE_USER":
        return "apple"
    return "password"

def extract_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        first_ip = forwarded_for.split(",")[0].strip()
        if first_ip:
            return first_ip
    true_client_ip = request.headers.get("true-client-ip")
    if true_client_ip:
        return true_client_ip.strip()
    cf_connecting_ip = request.headers.get("cf-connecting-ip")
    if cf_connecting_ip:
        return cf_connecting_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return ""

def build_device_info(user_agent: str) -> str:
    ua = (user_agent or "").lower()
    if not ua:
        return "Unknown device"
    platform = "Unknown device"
    browser = "Unknown browser"

    if "iphone" in ua:
        platform = "iPhone"
    elif "ipad" in ua:
        platform = "iPad"
    elif "android" in ua:
        platform = "Android"
    elif "windows" in ua:
        platform = "Windows"
    elif "mac os x" in ua or "macintosh" in ua:
        platform = "macOS"
    elif "linux" in ua:
        platform = "Linux"

    if "edg/" in ua:
        browser = "Edge"
    elif "opr/" in ua or "opera" in ua:
        browser = "Opera"
    elif "chrome/" in ua and "edg/" not in ua:
        browser = "Chrome"
    elif "firefox/" in ua:
        browser = "Firefox"
    elif "safari/" in ua and "chrome/" not in ua and "chromium/" not in ua:
        browser = "Safari"

    if platform == "Unknown device" and browser == "Unknown browser":
        return "Browser device"
    if browser == "Unknown browser":
        return platform
    if platform == "Unknown device":
        return browser
    return f"{platform} · {browser}"

def record_login_event(db, user_id: str, provider: str, request: Request):
    cur = db.cursor()
    user_agent = request.headers.get("user-agent", "")
    cur.execute(
        """
        INSERT INTO login_logs (user_id, login_provider, ip_address, user_agent, device_info, status)
        VALUES (%s::uuid, %s, %s, %s, %s, 'success')
        """,
        (user_id, provider, extract_client_ip(request), user_agent, build_device_info(user_agent))
    )

@router.get("/login-history/{user_id}")
async def get_login_history(user_id: str, db=Depends(get_db)):
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT log_id, login_provider, login_time, ip_address, user_agent, device_info, status
        FROM login_logs
        WHERE user_id::text = %s
        ORDER BY login_time DESC
        LIMIT 10
        """,
        (user_id,)
    )
    return {"logs": cur.fetchall()}

@router.get("/profile/{user_id}")
async def get_profile(user_id: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        "SELECT user_id, username, email, password_hash FROM users WHERE user_id::text = %s",
        (user_id,)
    )
    user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user_id": str(user[0]),
        "username": user[1] or "",
        "email": user[2],
        "login_provider": resolve_login_provider(user[3]),
    }

@router.put("/profile/{user_id}")
async def update_profile(user_id: str, req: UpdateProfileReq, db=Depends(get_db)):
    username = (req.username or "").strip()
    if len(username) < 2 or len(username) > 24:
        raise HTTPException(status_code=400, detail="Username must be 2-24 characters")
    if not re.fullmatch(r"[A-Za-z0-9_\-.\u4e00-\u9fff ]+", username):
        raise HTTPException(status_code=400, detail="Username contains unsupported characters")

    cur = db.cursor()
    cur.execute(
        "SELECT user_id FROM users WHERE lower(username) = lower(%s) AND user_id::text <> %s",
        (username, user_id)
    )
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Username already taken")

    cur.execute(
        "UPDATE users SET username = %s WHERE user_id::text = %s RETURNING user_id, username, email",
        (username, user_id)
    )
    user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.commit()
    return {
        "user_id": str(user[0]),
        "username": user[1] or "",
        "email": user[2],
    }

@router.put("/change-password/{user_id}")
async def change_password(user_id: str, req: ChangePasswordReq, db=Depends(get_db)):
    password_pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9])(?=\S+$).{8,32}$"
    if not re.match(password_pattern, req.new_password):
        raise HTTPException(status_code=400, detail="Password too weak")

    cur = db.cursor()
    cur.execute(
        "SELECT password_hash FROM users WHERE user_id::text = %s",
        (user_id,)
    )
    user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(req.current_password, user[0]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if req.current_password == req.new_password:
        raise HTTPException(status_code=400, detail="New password must be different")

    cur.execute(
        "UPDATE users SET password_hash = %s WHERE user_id::text = %s",
        (get_password_hash(req.new_password), user_id)
    )
    db.commit()
    return {"status": "success"}

@router.delete("/account/{user_id}")
async def delete_account(user_id: str, req: DeleteAccountReq, db=Depends(get_db)):
    if (req.confirm_text or "").strip().upper() != "DELETE":
        raise HTTPException(status_code=400, detail="Please type DELETE to confirm")

    cur = db.cursor()
    cur.execute(
        "SELECT email, password_hash FROM users WHERE user_id::text = %s",
        (user_id,)
    )
    user = cur.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    email, password_hash = user
    provider = resolve_login_provider(password_hash)
    if provider == "password":
        if not req.current_password:
            raise HTTPException(status_code=400, detail="Current password is required")
        if not verify_password(req.current_password, password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

    cur.execute("DELETE FROM verification_codes WHERE email = %s", (email,))
    cur.execute("DELETE FROM users WHERE user_id::text = %s", (user_id,))
    db.commit()
    return {"status": "success"}

def _get_mail_provider() -> str:
    provider = (get_env("MAIL_PROVIDER", default="smtp") or "smtp").strip().lower()
    if provider in {"gmail", "smtp"}:
        return "smtp"
    if provider == "resend":
        return "resend"
    raise HTTPException(status_code=500, detail="Unsupported mail provider")

def _send_email_via_smtp(to_email: str, subject: str, html_content: str):
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = get_env("MAIL_FROM", "MAIL_SMTP_FROM", default="")
    msg['To'] = to_email

    host = get_env("MAIL_SMTP_SERVER", "MAIL_SERVER")
    port = get_env_int("MAIL_SMTP_PORT", "MAIL_PORT", default=587)
    username = get_env("MAIL_SMTP_USERNAME", "MAIL_USERNAME")
    password = get_env("MAIL_SMTP_PASSWORD", "MAIL_PASSWORD")
    mail_from = get_env("MAIL_FROM", "MAIL_SMTP_FROM")
    use_ssl = get_env_bool("MAIL_SMTP_USE_SSL", "MAIL_USE_SSL", default=False)
    use_tls = get_env_bool("MAIL_SMTP_USE_TLS", "MAIL_USE_TLS", default=True)

    if not host or not username or not password or not mail_from:
        raise HTTPException(status_code=500, detail="SMTP mail config missing")

    try:
        print(f"📨 [SMTP] Sending auth email to={to_email} host={host} port={port} from={mail_from}")
        smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        with smtp_cls(host, port) as server:
            if use_tls and not use_ssl:
                server.starttls()
            server.login(username, password)
            server.send_message(msg)
        print(f"✅ [SMTP] Mail sent successfully to={to_email}")
    except Exception as e:
        print(f"❌ [SMTP] Mail send failed to={to_email}: {repr(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Mail failed (SMTP): {type(e).__name__}")

def _send_email_via_resend(to_email: str, subject: str, html_content: str):
    api_key = get_env("MAIL_RESEND_API_KEY", "RESEND_API_KEY")
    from_email = get_env("MAIL_RESEND_FROM", "RESEND_FROM", "MAIL_FROM", "MAIL_SMTP_FROM")
    audience = get_env("MAIL_RESEND_AUDIENCE", "RESEND_AUDIENCE")

    if not api_key or not from_email:
        raise HTTPException(status_code=500, detail="Resend mail config missing")

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html_content,
    }
    if audience:
        payload["audience"] = audience

    try:
        print(
            f"📨 [Resend] Sending auth email to={to_email} from={from_email} "
            f"provider=resend audience={audience or 'none'}"
        )
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20.0,
        )
        response.raise_for_status()
        print(f"✅ [Resend] Mail sent successfully to={to_email} response={response.text}")
    except httpx.HTTPStatusError as e:
        response_text = e.response.text if e.response is not None else ""
        status_code = e.response.status_code if e.response is not None else "unknown"
        print(
            f"❌ [Resend] HTTP error sending to={to_email} status={status_code} "
            f"body={response_text}"
        )
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Mail failed (Resend HTTP {status_code})")
    except Exception as e:
        print(f"❌ [Resend] Send failed to={to_email}: {repr(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Mail failed (Resend): {type(e).__name__}")

# --- 统一的高颜值邮件模板系统 ---
def send_auth_email(to_email: str, code: str, email_type: str = "signup", lang: str = "zh"):
    templates = {
        "signup": {
            "zh": {"subject": "Chilan LRS 账号激活", "title": "欢迎来到 Chilan LRS", "body": "您的账号注册验证码是：", "footer": "该验证码 10 分钟内有效。如果不是您本人操作，请忽略此邮件。"},
            "en": {"subject": "Chilan LRS Activation", "title": "Welcome to Chilan LRS", "body": "Your registration code is:", "footer": "Code valid for 10 mins. If this wasn't you, ignore this email."}
        },
        "reset": {
            "zh": {"subject": "Chilan LRS 密码重置", "title": "找回您的密码", "body": "您正在尝试重置密码，验证码是：", "footer": "如果您并未尝试重置密码，请忽略此邮件。"},
            "en": {"subject": "Chilan LRS Password Reset", "title": "Reset Password", "body": "Your reset code is:", "footer": "If you didn't request a reset, ignore this email."}
        }
    }
    l_key = lang[:2] if lang[:2] in ["zh", "en"] else "en"
    t = templates.get(email_type, templates["signup"]).get(l_key)
    
    # 恢复带阴影的卡片样式
    content = f"""
    <html>
        <body style="font-family: sans-serif; padding: 20px; line-height: 1.6; color: #334155;">
            <div style="max-width: 500px; margin: 0 auto; border: 1px solid #f1f5f9; border-radius: 20px; padding: 40px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
                <h2 style="color: #2563eb; margin-top: 0;">{t['title']}</h2>
                <p style="font-size: 16px;">{t['body']}</p>
                <div style="background: #f8fafc; padding: 20px; font-size: 32px; font-weight: 800; letter-spacing: 8px; text-align: center; border-radius: 12px; color: #1e293b; margin: 30px 0;">{code}</div>
                <p style="color: #94a3b8; font-size: 13px; margin-top: 30px; border-top: 1px solid #f1f5f9; padding-top: 20px;">{t['footer']}</p>
            </div>
        </body>
    </html>
    """
    provider = _get_mail_provider()
    print(
        f"🔐 [AuthMail] provider={provider} email_type={email_type} "
        f"lang={lang} to={to_email}"
    )
    if provider == "resend":
        _send_email_via_resend(to_email, t['subject'], content)
    else:
        _send_email_via_smtp(to_email, t['subject'], content)

# --- 路由接口 (已修正为 @router) ---
@router.post("/signup")
async def signup(req: SignupReq, db=Depends(get_db)):
    # 更友好的强密码规则：8-32 位，至少一个字母、一个数字、一个特殊字符，不允许空格
    password_pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9])(?=\S+$).{8,32}$"
    if not re.match(password_pattern, req.password): raise HTTPException(status_code=400, detail="Password too weak")
    cur = db.cursor(); code = f"{random.randint(100000, 999999)}"
    cur.execute("INSERT INTO users (username, email, password_hash, is_active) VALUES (%s, %s, %s, FALSE) ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash;", (req.email.split('@')[0], req.email, get_password_hash(req.password)))
    cur.execute("INSERT INTO verification_codes (email, code, created_at) VALUES (%s, %s, CURRENT_TIMESTAMP) ON CONFLICT (email) DO UPDATE SET code = EXCLUDED.code, created_at = CURRENT_TIMESTAMP;", (req.email, code))
    send_auth_email(req.email, code, "signup", req.lang)
    db.commit(); return {"status": "success"}

@router.post("/verify")
async def verify(req: VerifyReq, db=Depends(get_db)):
    cur = db.cursor(); cur.execute("SELECT code FROM verification_codes WHERE email = %s", (req.email,))
    row = cur.fetchone()
    if not row or row[0] != req.code: raise HTTPException(status_code=400, detail="Invalid code")
    cur.execute("UPDATE users SET is_active = TRUE WHERE email = %s", (req.email,))
    cur.execute("DELETE FROM verification_codes WHERE email = %s", (req.email,)); db.commit()
    return {"status": "success"}

@router.post("/login")
async def login(req: LoginReq, request: Request, db=Depends(get_db)):
    cur = db.cursor(); cur.execute("SELECT user_id, username, email, password_hash, is_active FROM users WHERE email = %s", (req.email,))
    user = cur.fetchone()
    if not user or not verify_password(req.password, user[3]): raise HTTPException(status_code=400, detail="Invalid credentials")
    if not user[4]: raise HTTPException(status_code=403, detail="Not activated")
    provider = resolve_login_provider(user[3])
    record_login_event(db, str(user[0]), provider, request)
    db.commit()
    return {
        "status": "success",
        "access_token": create_access_token({"sub": str(user[0])}),
        "user_id": str(user[0]),
        "username": user[1] or "",
        "email": user[2],
        "login_provider": provider,
    }

@router.post("/forgot-password")
async def forgot_password(req: ForgotReq, db=Depends(get_db)):
    cur = db.cursor(); cur.execute("SELECT user_id FROM users WHERE email = %s AND is_active = TRUE", (req.email,))
    if not cur.fetchone(): raise HTTPException(status_code=404, detail="Email not found")
    code = f"{random.randint(100000, 999999)}"
    cur.execute("INSERT INTO verification_codes (email, code, created_at) VALUES (%s, %s, CURRENT_TIMESTAMP) ON CONFLICT (email) DO UPDATE SET code = EXCLUDED.code, created_at = CURRENT_TIMESTAMP;", (req.email, code))
    send_auth_email(req.email, code, "reset", "zh"); db.commit(); return {"status": "success"}

@router.post("/reset-password")
async def reset_password(req: ResetReq, db=Depends(get_db)):
    cur = db.cursor(); cur.execute("SELECT code FROM verification_codes WHERE email = %s", (req.email,))
    row = cur.fetchone()
    if not row or row[0] != req.code: raise HTTPException(status_code=400, detail="Invalid code")
    cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", (get_password_hash(req.new_password), req.email))
    cur.execute("DELETE FROM verification_codes WHERE email = %s", (req.email,)); db.commit(); return {"status": "success"}

@router.post("/google")
async def google_auth(req: GoogleAuthReq, request: Request, db=Depends(get_db)):
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://www.googleapis.com/oauth2/v3/userinfo", headers={"Authorization": f"Bearer {req.access_token}"})
        if resp.status_code != 200: raise HTTPException(status_code=400, detail="Google token invalid")
        data = resp.json()
    cur = db.cursor(); cur.execute("SELECT user_id FROM users WHERE email = %s", (data['email'],))
    user = cur.fetchone()
    if not user:
        cur.execute("INSERT INTO users (username, email, password_hash, is_active) VALUES (%s, %s, 'GOOGLE_USER', TRUE) RETURNING user_id", (data.get('name', data['email']), data['email']))
        user_id = str(cur.fetchone()[0]); db.commit()
        username = data.get('name', data['email'])
    else:
        user_id = str(user[0])
        username = data.get('name', data['email'])
    record_login_event(db, user_id, "google", request)
    db.commit()
    return {
        "status": "success",
        "access_token": create_access_token({"sub": user_id}),
        "user_id": user_id,
        "username": username or "",
        "email": data['email'],
        "login_provider": "google",
    }

@router.post("/apple")
async def apple_auth(req: AppleAuthReq, request: Request, db=Depends(get_db)):
    jwks_client = PyJWKClient("https://appleid.apple.com/auth/keys")
    try:
        idinfo = jwt.decode(
            req.token,
            jwks_client.get_signing_key_from_jwt(req.token).key,
            algorithms=["RS256"],
            audience=get_env("AUTH_APPLE_CLIENT_ID", "APPLE_CLIENT_ID"),
            issuer="https://appleid.apple.com"
        )
        email = idinfo.get('email') or f"{idinfo['sub']}@apple.chilan"
        cur = db.cursor(); cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if not user:
            username = f"{req.firstName or ''} {req.lastName or ''}".strip() or email.split('@')[0]
            cur.execute("INSERT INTO users (username, email, password_hash, is_active) VALUES (%s, %s, 'APPLE_USER', TRUE) RETURNING user_id", (username, email))
            user_id = str(cur.fetchone()[0]); db.commit()
        else:
            user_id = str(user[0])
            username = f"{req.firstName or ''} {req.lastName or ''}".strip() or email.split('@')[0]
        record_login_event(db, user_id, "apple", request)
        db.commit()
        return {
            "status": "success",
            "access_token": create_access_token({"sub": user_id}),
            "user_id": user_id,
            "username": username or "",
            "email": email,
            "login_provider": "apple",
        }
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))
