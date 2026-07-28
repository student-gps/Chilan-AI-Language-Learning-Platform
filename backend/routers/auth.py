import re, random, httpx, jwt, smtplib, traceback
from datetime import datetime, timezone
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


def build_login_context(request: Request) -> dict:
    user_agent = request.headers.get("user-agent", "")
    return {
        "ip_address": extract_client_ip(request),
        "user_agent": user_agent,
        "device_info": build_device_info(user_agent),
    }


def record_login_event(db, user_id: str, provider: str, login_context: dict):
    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO login_logs (user_id, login_provider, ip_address, user_agent, device_info, status)
        VALUES (%s::uuid, %s, %s, %s, %s, 'success')
        """,
        (
            user_id,
            provider,
            login_context.get("ip_address", ""),
            login_context.get("user_agent", ""),
            login_context.get("device_info", "Unknown device"),
        )
    )


def get_recent_successful_login_logs(db, user_id: str, limit: int = 10):
    cur = db.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        """
        SELECT ip_address, user_agent, device_info, login_provider, login_time
        FROM login_logs
        WHERE user_id::text = %s AND status = 'success'
        ORDER BY login_time DESC
        LIMIT %s
        """,
        (user_id, limit)
    )
    return cur.fetchall() or []


def is_unusual_login(recent_logs, login_context: dict) -> bool:
    current_ip = (login_context.get("ip_address") or "").strip()
    current_device = (login_context.get("device_info") or "").strip()
    if not recent_logs or not current_ip or not current_device or current_device == "Unknown device":
        return False

    seen_ips = {
        (row.get("ip_address") or "").strip()
        for row in recent_logs
        if isinstance(row, dict) and (row.get("ip_address") or "").strip()
    }
    seen_devices = {
        (row.get("device_info") or "").strip()
        for row in recent_logs
        if isinstance(row, dict) and (row.get("device_info") or "").strip()
    }
    return current_ip not in seen_ips and current_device not in seen_devices


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
    if not re.fullmatch(r"[A-Za-z0-9_\-.一-鿿 ]+", username):
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
async def change_password(user_id: str, req: ChangePasswordReq, request: Request, db=Depends(get_db)):
    password_pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9])(?=\S+$).{8,32}$"
    if not re.match(password_pattern, req.new_password):
        raise HTTPException(status_code=400, detail="Password too weak")

    cur = db.cursor()
    cur.execute(
        "SELECT password_hash, email FROM users WHERE user_id::text = %s",
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
    try_send_password_changed_email(
        user[1],
        lang=infer_mail_lang_from_request(request),
        change_source="change",
        login_context=build_login_context(request),
    )
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
    msg['From'] = get_env("MAIL_SMTP_FROM", default="")
    msg['To'] = to_email

    host = get_env("MAIL_SMTP_SERVER")
    port = get_env_int("MAIL_SMTP_PORT", default=587)
    username = get_env("MAIL_SMTP_USERNAME")
    password = get_env("MAIL_SMTP_PASSWORD")
    mail_from = get_env("MAIL_SMTP_FROM")
    use_ssl = get_env_bool("MAIL_SMTP_USE_SSL", default=False)
    use_tls = get_env_bool("MAIL_SMTP_USE_TLS", default=True)

    if not host or not username or not password or not mail_from:
        raise HTTPException(status_code=500, detail="SMTP mail config missing")

    try:
        print(f"[auth-mail][smtp] sending to={to_email} host={host} port={port} from={mail_from}")
        smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        with smtp_cls(host, port) as server:
            if use_tls and not use_ssl:
                server.starttls()
            server.login(username, password)
            server.send_message(msg)
        print(f"[auth-mail][smtp] sent to={to_email}")
    except Exception as e:
        print(f"[auth-mail][smtp] failed to={to_email}: {repr(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Mail failed (SMTP): {type(e).__name__}")


def _send_email_via_resend(to_email: str, subject: str, html_content: str):
    api_key = get_env("MAIL_RESEND_API_KEY")
    from_email = get_env("MAIL_RESEND_FROM")
    audience = get_env("MAIL_RESEND_AUDIENCE")

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
            f"[auth-mail][resend] sending to={to_email} from={from_email} "
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
        print(f"[auth-mail][resend] sent to={to_email} response={response.text}")
    except httpx.HTTPStatusError as e:
        response_text = e.response.text if e.response is not None else ""
        status_code = e.response.status_code if e.response is not None else "unknown"
        print(
            f"[auth-mail][resend] http-error to={to_email} status={status_code} "
            f"body={response_text}"
        )
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Mail failed (Resend HTTP {status_code})")
    except Exception as e:
        print(f"[auth-mail][resend] failed to={to_email}: {repr(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Mail failed (Resend): {type(e).__name__}")


AUTH_EMAIL_TEMPLATES = {
    "signup": {
        "zh": {
            "subject": "Chilan LRS 账号激活",
            "title": "欢迎来到 Chilan LRS",
            "body": "您的账号注册验证码是：",
            "footer": "该验证码 10 分钟内有效。如果不是您本人操作，请忽略此邮件。",
        },
        "en": {
            "subject": "Chilan LRS Activation",
            "title": "Welcome to Chilan LRS",
            "body": "Your registration code is:",
            "footer": "Code valid for 10 mins. If this wasn't you, ignore this email.",
        },
    },
    "reset": {
        "zh": {
            "subject": "Chilan LRS 密码重置",
            "title": "找回您的密码",
            "body": "您正在尝试重置密码，验证码是：",
            "footer": "如果您并未尝试重置密码，请忽略此邮件。",
        },
        "en": {
            "subject": "Chilan LRS Password Reset",
            "title": "Reset Password",
            "body": "Your reset code is:",
            "footer": "If you didn't request a reset, ignore this email.",
        },
    },
    "unusual_login": {
        "zh": {
            "subject": "Chilan LRS 登录安全提醒",
            "title": "检测到新的登录环境",
            "body": "你的账号刚刚在新的设备和网络环境中完成登录。",
            "footer": "如果这是你本人操作，无需进一步处理；如果不是，请尽快修改密码并检查最近登录记录。",
        },
        "en": {
            "subject": "Chilan LRS Sign-in Security Alert",
            "title": "We noticed a new sign-in environment",
            "body": "Your account just signed in from a new device and network environment.",
            "footer": "If this was you, no action is needed. If not, please reset your password and review recent sign-ins.",
        },
    },
    "password_changed_success": {
        "zh": {
            "subject": "Chilan LRS 密码已更新",
            "title": "你的密码已成功更新",
            "body": "你的 Chilan LRS 账号密码刚刚被成功修改。",
            "footer": "如果这不是你本人操作，请立即重置密码并检查最近登录记录。",
        },
        "en": {
            "subject": "Chilan LRS Password Updated",
            "title": "Your password was changed successfully",
            "body": "Your Chilan LRS account password was just updated successfully.",
            "footer": "If this wasn't you, reset your password immediately and review recent sign-ins.",
        },
    },
}


def infer_mail_lang_from_request(request: Request | None, fallback: str = "zh") -> str:
    if request is None:
        return fallback
    header = (request.headers.get("accept-language") or "").strip().lower()
    if not header:
        return fallback
    primary = header.split(",", 1)[0].split("-", 1)[0].strip()
    return primary if primary in {"zh", "en"} else fallback


def _now_utc_label() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _translate_login_provider(provider: str, lang: str) -> str:
    normalized = (provider or "password").strip().lower()
    if lang == "zh":
        mapping = {"password": "邮箱密码", "google": "Google", "apple": "Apple"}
    else:
        mapping = {"password": "Email & Password", "google": "Google", "apple": "Apple"}
    return mapping.get(normalized, normalized or ("未知" if lang == "zh" else "Unknown"))


def _translate_password_change_source(change_source: str, lang: str) -> str:
    normalized = (change_source or "change").strip().lower()
    if lang == "zh":
        mapping = {"reset": "通过邮箱验证码重置", "change": "在账号设置中修改"}
    else:
        mapping = {"reset": "Reset via email verification", "change": "Changed from account settings"}
    return mapping.get(normalized, mapping["change"])


def _build_auth_mail_html(template: dict, highlight_value: str, details=None, highlight_is_code: bool = False) -> str:
    highlight_value = (highlight_value or "").strip()
    cleaned_details = []
    for item in details or []:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            continue
        label = str(item[0] or "").strip()
        value = str(item[1] or "").strip()
        if label and value:
            cleaned_details.append((label, value))

    if highlight_value:
        if highlight_is_code:
            highlight_style = (
                "background: #f8fafc; padding: 20px; font-size: 32px; font-weight: 800; "
                "letter-spacing: 8px; text-align: center; border-radius: 12px; color: #1e293b; margin: 30px 0;"
            )
        else:
            highlight_style = (
                "background: #f8fafc; padding: 20px; font-size: 24px; font-weight: 800; "
                "text-align: center; border-radius: 12px; color: #1e293b; margin: 30px 0;"
            )
        highlight_html = f'<div style="{highlight_style}">{highlight_value}</div>'
    else:
        highlight_html = ""

    if cleaned_details:
        rows = []
        for index, (label, value) in enumerate(cleaned_details):
            border = "border-top: 1px solid #e2e8f0;" if index > 0 else ""
            rows.append(
                f'<div style="display: flex; justify-content: space-between; gap: 16px; padding: 12px 0; {border}">'
                f'<span style="font-size: 13px; color: #64748b; font-weight: 700;">{label}</span>'
                f'<span style="font-size: 14px; color: #1e293b; font-weight: 700; text-align: right;">{value}</span>'
                f'</div>'
            )
        details_html = (
            '<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; padding: 0 18px; margin-top: 24px;">'
            + "".join(rows)
            + '</div>'
        )
    else:
        details_html = ""

    return f"""
    <html>
        <body style="font-family: sans-serif; padding: 20px; line-height: 1.6; color: #334155;">
            <div style="max-width: 500px; margin: 0 auto; border: 1px solid #f1f5f9; border-radius: 20px; padding: 40px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
                <h2 style="color: #2563eb; margin-top: 0;">{template['title']}</h2>
                <p style="font-size: 16px;">{template['body']}</p>
                {highlight_html}
                {details_html}
                <p style="color: #94a3b8; font-size: 13px; margin-top: 30px; border-top: 1px solid #f1f5f9; padding-top: 20px;">{template['footer']}</p>
            </div>
        </body>
    </html>
    """


def send_auth_email(
    to_email: str,
    highlight_value: str,
    email_type: str = "signup",
    lang: str = "zh",
    details=None,
    highlight_is_code: bool | None = None,
):
    lang_key = lang[:2] if lang[:2] in ["zh", "en"] else "en"
    template_group = AUTH_EMAIL_TEMPLATES.get(email_type)
    if not template_group:
        raise ValueError(f"Unsupported auth email type: {email_type}")
    template = template_group.get(lang_key, template_group.get("en"))
    if highlight_is_code is None:
        highlight_is_code = email_type in {"signup", "reset"}

    content = _build_auth_mail_html(
        template,
        highlight_value=highlight_value,
        details=details,
        highlight_is_code=highlight_is_code,
    )
    provider = _get_mail_provider()
    print(
        f"[auth-mail] provider={provider} email_type={email_type} "
        f"lang={lang_key} to={to_email}"
    )
    if provider == "resend":
        _send_email_via_resend(to_email, template['subject'], content)
    else:
        _send_email_via_smtp(to_email, template['subject'], content)


def try_send_auth_email(*args, **kwargs):
    try:
        send_auth_email(*args, **kwargs)
    except Exception as e:
        email_type = kwargs.get("email_type") or (args[2] if len(args) > 2 else "unknown")
        print(f"[auth-mail] non-blocking send failed for type={email_type}: {repr(e)}")
        traceback.print_exc()


def try_send_unusual_login_email(to_email: str, provider: str, login_context: dict, lang: str = "zh"):
    if lang == "zh":
        details = [
            ("登录方式", _translate_login_provider(provider, lang)),
            ("设备", login_context.get("device_info") or "Unknown device"),
            ("IP", login_context.get("ip_address") or "Unknown"),
            ("时间", _now_utc_label()),
        ]
        highlight_value = login_context.get("device_info") or "新登录提醒"
    else:
        details = [
            ("Sign-in method", _translate_login_provider(provider, lang)),
            ("Device", login_context.get("device_info") or "Unknown device"),
            ("IP", login_context.get("ip_address") or "Unknown"),
            ("Time", _now_utc_label()),
        ]
        highlight_value = login_context.get("device_info") or "New sign-in detected"

    try_send_auth_email(
        to_email,
        highlight_value,
        email_type="unusual_login",
        lang=lang,
        details=details,
        highlight_is_code=False,
    )


def try_send_password_changed_email(
    to_email: str,
    lang: str = "zh",
    change_source: str = "change",
    login_context: dict | None = None,
):
    login_context = login_context or {}
    if lang == "zh":
        details = [
            ("变更方式", _translate_password_change_source(change_source, lang)),
            ("时间", _now_utc_label()),
        ]
        if login_context.get("device_info"):
            details.append(("设备", login_context.get("device_info")))
        if login_context.get("ip_address"):
            details.append(("IP", login_context.get("ip_address")))
        highlight_value = "密码更新成功"
    else:
        details = [
            ("Change source", _translate_password_change_source(change_source, lang)),
            ("Time", _now_utc_label()),
        ]
        if login_context.get("device_info"):
            details.append(("Device", login_context.get("device_info")))
        if login_context.get("ip_address"):
            details.append(("IP", login_context.get("ip_address")))
        highlight_value = "Password updated"

    try_send_auth_email(
        to_email,
        highlight_value,
        email_type="password_changed_success",
        lang=lang,
        details=details,
        highlight_is_code=False,
    )


# --- 路由接口 (已修正为 @router) ---
@router.post("/signup")
async def signup(req: SignupReq, db=Depends(get_db)):
    password_pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9])(?=\S+$).{8,32}$"
    if not re.match(password_pattern, req.password):
        raise HTTPException(status_code=400, detail="Password too weak")
    cur = db.cursor()
    code = f"{random.randint(100000, 999999)}"
    cur.execute(
        "INSERT INTO users (username, email, password_hash, is_active) VALUES (%s, %s, %s, FALSE) ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash;",
        (req.email.split('@')[0], req.email, get_password_hash(req.password))
    )
    cur.execute(
        "INSERT INTO verification_codes (email, code, created_at) VALUES (%s, %s, CURRENT_TIMESTAMP) ON CONFLICT (email) DO UPDATE SET code = EXCLUDED.code, created_at = CURRENT_TIMESTAMP;",
        (req.email, code)
    )
    send_auth_email(req.email, code, "signup", req.lang)
    db.commit()
    return {"status": "success"}


@router.post("/verify")
async def verify(req: VerifyReq, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT code FROM verification_codes WHERE email = %s", (req.email,))
    row = cur.fetchone()
    if not row or row[0] != req.code:
        raise HTTPException(status_code=400, detail="Invalid code")
    cur.execute("UPDATE users SET is_active = TRUE WHERE email = %s", (req.email,))
    cur.execute("DELETE FROM verification_codes WHERE email = %s", (req.email,))
    db.commit()
    return {"status": "success"}


@router.post("/login")
async def login(req: LoginReq, request: Request, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT user_id, username, email, password_hash, is_active FROM users WHERE email = %s", (req.email,))
    user = cur.fetchone()
    if not user or not verify_password(req.password, user[3]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not user[4]:
        raise HTTPException(status_code=403, detail="Not activated")

    user_id = str(user[0])
    provider = resolve_login_provider(user[3])
    login_context = build_login_context(request)
    recent_logs = get_recent_successful_login_logs(db, user_id)
    should_alert = is_unusual_login(recent_logs, login_context)

    record_login_event(db, user_id, provider, login_context)
    db.commit()

    if should_alert:
        try_send_unusual_login_email(
            user[2],
            provider=provider,
            login_context=login_context,
            lang=infer_mail_lang_from_request(request),
        )

    return {
        "status": "success",
        "access_token": create_access_token({"sub": user_id}),
        "user_id": user_id,
        "username": user[1] or "",
        "email": user[2],
        "login_provider": provider,
    }


@router.post("/forgot-password")
async def forgot_password(req: ForgotReq, request: Request, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT user_id FROM users WHERE email = %s AND is_active = TRUE", (req.email,))
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Email not found")
    code = f"{random.randint(100000, 999999)}"
    cur.execute(
        "INSERT INTO verification_codes (email, code, created_at) VALUES (%s, %s, CURRENT_TIMESTAMP) ON CONFLICT (email) DO UPDATE SET code = EXCLUDED.code, created_at = CURRENT_TIMESTAMP;",
        (req.email, code)
    )
    send_auth_email(req.email, code, "reset", infer_mail_lang_from_request(request))
    db.commit()
    return {"status": "success"}


@router.post("/reset-password")
async def reset_password(req: ResetReq, request: Request, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT code FROM verification_codes WHERE email = %s", (req.email,))
    row = cur.fetchone()
    if not row or row[0] != req.code:
        raise HTTPException(status_code=400, detail="Invalid code")
    cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", (get_password_hash(req.new_password), req.email))
    cur.execute("DELETE FROM verification_codes WHERE email = %s", (req.email,))
    db.commit()
    try_send_password_changed_email(
        req.email,
        lang=infer_mail_lang_from_request(request),
        change_source="reset",
        login_context=build_login_context(request),
    )
    return {"status": "success"}


@router.post("/google")
async def google_auth(req: GoogleAuthReq, request: Request, db=Depends(get_db)):
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://www.googleapis.com/oauth2/v3/userinfo", headers={"Authorization": f"Bearer {req.access_token}"})
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Google token invalid")
        data = resp.json()

    cur = db.cursor()
    cur.execute("SELECT user_id FROM users WHERE email = %s", (data['email'],))
    user = cur.fetchone()
    if not user:
        cur.execute(
            "INSERT INTO users (username, email, password_hash, is_active) VALUES (%s, %s, 'GOOGLE_USER', TRUE) RETURNING user_id",
            (data.get('name', data['email']), data['email'])
        )
        user_id = str(cur.fetchone()[0])
        username = data.get('name', data['email'])
    else:
        user_id = str(user[0])
        username = data.get('name', data['email'])

    login_context = build_login_context(request)
    recent_logs = get_recent_successful_login_logs(db, user_id)
    should_alert = is_unusual_login(recent_logs, login_context)

    record_login_event(db, user_id, "google", login_context)
    db.commit()

    if should_alert:
        try_send_unusual_login_email(
            data['email'],
            provider="google",
            login_context=login_context,
            lang=infer_mail_lang_from_request(request),
        )

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
            audience=get_env("AUTH_APPLE_CLIENT_ID"),
            issuer="https://appleid.apple.com"
        )
        email = idinfo.get('email') or f"{idinfo['sub']}@apple.chilan"
        cur = db.cursor()
        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if not user:
            username = f"{req.firstName or ''} {req.lastName or ''}".strip() or email.split('@')[0]
            cur.execute(
                "INSERT INTO users (username, email, password_hash, is_active) VALUES (%s, %s, 'APPLE_USER', TRUE) RETURNING user_id",
                (username, email)
            )
            user_id = str(cur.fetchone()[0])
        else:
            user_id = str(user[0])
            username = f"{req.firstName or ''} {req.lastName or ''}".strip() or email.split('@')[0]

        login_context = build_login_context(request)
        recent_logs = get_recent_successful_login_logs(db, user_id)
        should_alert = is_unusual_login(recent_logs, login_context)

        record_login_event(db, user_id, "apple", login_context)
        db.commit()

        if should_alert:
            try_send_unusual_login_email(
                email,
                provider="apple",
                login_context=login_context,
                lang=infer_mail_lang_from_request(request),
            )

        return {
            "status": "success",
            "access_token": create_access_token({"sub": user_id}),
            "user_id": user_id,
            "username": username or "",
            "email": email,
            "login_provider": "apple",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
