import os, re, random, httpx, jwt, smtplib
from email.mime.text import MIMEText
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from jwt import PyJWKClient
from database.connection import get_connection
from database.utils import get_password_hash, verify_password, create_access_token

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

def get_db():
    conn = get_connection()
    try: yield conn
    finally: conn.close()

def _get_mail_provider() -> str:
    provider = (os.getenv("MAIL_PROVIDER") or "smtp").strip().lower()
    if provider in {"gmail", "smtp"}:
        return "smtp"
    if provider == "resend":
        return "resend"
    raise HTTPException(status_code=500, detail="Unsupported mail provider")

def _send_email_via_smtp(to_email: str, subject: str, html_content: str):
    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = os.getenv("MAIL_FROM")
    msg['To'] = to_email

    host = os.getenv("MAIL_SERVER")
    port = int(os.getenv("MAIL_PORT", "587"))
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    use_ssl = (os.getenv("MAIL_USE_SSL", "false").strip().lower() == "true")
    use_tls = (os.getenv("MAIL_USE_TLS", "true").strip().lower() == "true")

    if not host or not username or not password or not os.getenv("MAIL_FROM"):
        raise HTTPException(status_code=500, detail="SMTP mail config missing")

    try:
        smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        with smtp_cls(host, port) as server:
            if use_tls and not use_ssl:
                server.starttls()
            server.login(username, password)
            server.send_message(msg)
    except Exception:
        raise HTTPException(status_code=500, detail="Mail failed")

def _send_email_via_resend(to_email: str, subject: str, html_content: str):
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM") or os.getenv("MAIL_FROM")
    audience = os.getenv("RESEND_AUDIENCE")

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
    except Exception:
        raise HTTPException(status_code=500, detail="Mail failed")

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
    if provider == "resend":
        _send_email_via_resend(to_email, t['subject'], content)
    else:
        _send_email_via_smtp(to_email, t['subject'], content)

# --- 路由接口 (已修正为 @router) ---
@router.post("/signup")
async def signup(req: SignupReq, db=Depends(get_db)):
    password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,20}$"
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
async def login(req: LoginReq, db=Depends(get_db)):
    cur = db.cursor(); cur.execute("SELECT user_id, password_hash, is_active FROM users WHERE email = %s", (req.email,))
    user = cur.fetchone()
    if not user or not verify_password(req.password, user[1]): raise HTTPException(status_code=400, detail="Invalid credentials")
    if not user[2]: raise HTTPException(status_code=403, detail="Not activated")
    return {"status": "success", "access_token": create_access_token({"sub": str(user[0])}), "user_id": str(user[0])}

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
async def google_auth(req: GoogleAuthReq, db=Depends(get_db)):
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://www.googleapis.com/oauth2/v3/userinfo", headers={"Authorization": f"Bearer {req.access_token}"})
        if resp.status_code != 200: raise HTTPException(status_code=400, detail="Google token invalid")
        data = resp.json()
    cur = db.cursor(); cur.execute("SELECT user_id FROM users WHERE email = %s", (data['email'],))
    user = cur.fetchone()
    if not user:
        cur.execute("INSERT INTO users (username, email, password_hash, is_active) VALUES (%s, %s, 'GOOGLE_USER', TRUE) RETURNING user_id", (data.get('name', data['email']), data['email']))
        user_id = str(cur.fetchone()[0]); db.commit()
    else: user_id = str(user[0])
    return {"status": "success", "access_token": create_access_token({"sub": user_id}), "user_id": user_id}

@router.post("/apple")
async def apple_auth(req: AppleAuthReq, db=Depends(get_db)):
    jwks_client = PyJWKClient("https://appleid.apple.com/auth/keys")
    try:
        idinfo = jwt.decode(req.token, jwks_client.get_signing_key_from_jwt(req.token).key, algorithms=["RS256"], audience=os.getenv("APPLE_CLIENT_ID"), issuer="https://appleid.apple.com")
        email = idinfo.get('email') or f"{idinfo['sub']}@apple.chilan"
        cur = db.cursor(); cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if not user:
            cur.execute("INSERT INTO users (username, email, password_hash, is_active) VALUES (%s, %s, 'APPLE_USER', TRUE) RETURNING user_id", (f"{req.firstName or ''} {req.lastName or ''}".strip() or email.split('@')[0], email))
            user_id = str(cur.fetchone()[0]); db.commit()
        else: user_id = str(user[0])
        return {"status": "success", "access_token": create_access_token({"sub": user_id}), "user_id": user_id}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))
