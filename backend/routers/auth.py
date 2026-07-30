import re, random, httpx, jwt, smtplib, traceback
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr
from jwt import PyJWKClient
from psycopg2.extras import RealDictCursor
from database.connection import get_connection
from database.utils import get_password_hash, verify_password, create_access_token
from config.env import get_env, get_env_bool, get_env_int

router = APIRouter(prefix="/auth", tags=["Authentication"])


class SignupReq(BaseModel):
    email: EmailStr
    password: str
    lang: str | None = None


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


INTERFACE_LANGUAGE_HEADER = "X-Chilan-Interface-Language"
AUTH_EMAIL_DEFAULT_LANG = "en"
AUTH_EMAIL_UNSUPPORTED_FALLBACK_LANG = "en"
VERIFICATION_CODE_TTL_MINUTES = 10
VERIFICATION_CODE_TTL = timedelta(minutes=VERIFICATION_CODE_TTL_MINUTES)


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


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


def _verification_code_expired(created_at) -> bool:
    if created_at is None:
        return True
    if isinstance(created_at, datetime):
        created_dt = created_at
    else:
        return True
    if created_dt.tzinfo is None:
        created_dt = created_dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - created_dt > VERIFICATION_CODE_TTL


def _delete_verification_code(db, email: str):
    cur = db.cursor()
    cur.execute("DELETE FROM verification_codes WHERE email = %s", (email,))


def _delete_expired_verification_code(db, email: str):
    _delete_verification_code(db, email)


def _verification_code_error_message(kind: str, lang: str) -> str:
    lang_key = normalize_auth_email_lang(lang) or AUTH_EMAIL_UNSUPPORTED_FALLBACK_LANG
    messages = {
        "invalid": {
            "zh": "验证码无效，请重新输入。",
            "en": "Invalid verification code. Please try again.",
            "ja": "認証コードが正しくありません。もう一度入力してください。",
            "fr": "Code de vérification invalide. Veuillez réessayer.",
            "de": "Ungültiger Bestätigungscode. Bitte versuchen Sie es erneut.",
            "ko": "인증 코드가 올바르지 않습니다. 다시 시도해 주세요.",
            "es": "Código de verificación no válido. Inténtalo de nuevo.",
            "vi": "Mã xác minh không hợp lệ. Vui lòng thử lại.",
            "pt": "Código de verificação inválido. Tente novamente.",
            "ar": "رمز التحقق غير صالح. يُرجى المحاولة مرة أخرى.",
            "th": "รหัสยืนยันไม่ถูกต้อง กรุณาลองอีกครั้ง",
            "ru": "Неверный код подтверждения. Попробуйте ещё раз.",
            "id": "Kode verifikasi tidak valid. Silakan coba lagi.",
            "ms": "Kod pengesahan tidak sah. Sila cuba lagi.",
            "it": "Codice di verifica non valido. Riprova.",
        },
        "expired": {
            "zh": f"验证码已过期，请重新获取。该验证码有效期为 {VERIFICATION_CODE_TTL_MINUTES} 分钟。",
            "en": f"Verification code expired. Please request a new code. Valid for {VERIFICATION_CODE_TTL_MINUTES} minutes.",
            "ja": f"認証コードの有効期限が切れています。新しいコードを再取得してください。このコードの有効期間は {VERIFICATION_CODE_TTL_MINUTES} 分です。",
            "fr": f"Le code de vérification a expiré. Veuillez demander un nouveau code. Durée de validité : {VERIFICATION_CODE_TTL_MINUTES} minutes.",
            "de": f"Der Bestätigungscode ist abgelaufen. Bitte fordern Sie einen neuen Code an. Gültig für {VERIFICATION_CODE_TTL_MINUTES} Minuten.",
            "ko": f"인증 코드가 만료되었습니다. 새 코드를 다시 요청해 주세요. 유효 시간은 {VERIFICATION_CODE_TTL_MINUTES}분입니다.",
            "es": f"El código de verificación ha caducado. Solicita un código nuevo. Válido durante {VERIFICATION_CODE_TTL_MINUTES} minutos.",
            "vi": f"Mã xác minh đã hết hạn. Vui lòng yêu cầu mã mới. Mã có hiệu lực trong {VERIFICATION_CODE_TTL_MINUTES} phút.",
            "pt": f"O código de verificação expirou. Solicite um novo código. Válido por {VERIFICATION_CODE_TTL_MINUTES} minutos.",
            "ar": f"انتهت صلاحية رمز التحقق. يُرجى طلب رمز جديد. مدة الصلاحية {VERIFICATION_CODE_TTL_MINUTES} دقائق.",
            "th": f"รหัสยืนยันหมดอายุแล้ว กรุณาขอรหัสใหม่ รหัสนี้มีอายุ {VERIFICATION_CODE_TTL_MINUTES} นาที",
            "ru": f"Срок действия кода подтверждения истёк. Запросите новый код. Код действителен {VERIFICATION_CODE_TTL_MINUTES} минут.",
            "id": f"Kode verifikasi telah kedaluwarsa. Silakan minta kode baru. Berlaku selama {VERIFICATION_CODE_TTL_MINUTES} menit.",
            "ms": f"Kod pengesahan telah tamat tempoh. Sila minta kod baharu. Sah selama {VERIFICATION_CODE_TTL_MINUTES} minit.",
            "it": f"Il codice di verifica è scaduto. Richiedi un nuovo codice. Valido per {VERIFICATION_CODE_TTL_MINUTES} minuti.",
        },
    }
    bucket = messages.get(kind, messages["invalid"])
    return bucket.get(lang_key, bucket[AUTH_EMAIL_UNSUPPORTED_FALLBACK_LANG])


def _raise_if_verification_code_invalid(db, email: str, row, submitted_code: str, lang: str):
    if not row or row[0] != submitted_code:
        raise HTTPException(status_code=400, detail=_verification_code_error_message("invalid", lang))
    created_at = row[1] if len(row) > 1 else None
    if _verification_code_expired(created_at):
        _delete_expired_verification_code(db, email)
        db.commit()
        raise HTTPException(status_code=400, detail=_verification_code_error_message("expired", lang))


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
        lang=resolve_auth_email_lang(request=request),
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


def _auth_template(subject: str, title: str, body: str, footer: str) -> dict:
    return {
        "subject": subject,
        "title": title,
        "body": body,
        "footer": footer,
    }


AUTH_EMAIL_TEMPLATES = {
    "signup": {
        "zh": _auth_template("Chilan LRS 账号激活", "欢迎来到 Chilan LRS", "您的账号注册验证码是：", "该验证码 10 分钟内有效。如果不是您本人操作，请忽略此邮件。"),
        "en": _auth_template("Chilan LRS Activation", "Welcome to Chilan LRS", "Your registration code is:", "Code valid for 10 mins. If this wasn't you, ignore this email."),
        "ja": _auth_template("Chilan LRS アカウント認証", "Chilan LRS へようこそ", "アカウント登録確認コードはこちらです：", "このコードは10分間有効です。心当たりがない場合は、このメールを無視してください。"),
        "fr": _auth_template("Activation du compte Chilan LRS", "Bienvenue sur Chilan LRS", "Voici votre code de vérification d'inscription :", "Ce code est valable 10 minutes. Si ce n'était pas vous, ignorez cet e-mail."),
        "de": _auth_template("Chilan LRS Kontoaktivierung", "Willkommen bei Chilan LRS", "Hier ist Ihr Registrierungscode:", "Dieser Code ist 10 Minuten gültig. Wenn Sie das nicht waren, ignorieren Sie diese E-Mail."),
        "ko": _auth_template("Chilan LRS 계정 인증", "Chilan LRS에 오신 것을 환영합니다", "회원가입 인증 코드는 다음과 같습니다:", "이 코드는 10분 동안 유효합니다. 본인이 아니라면 이 메일을 무시하세요."),
        "es": _auth_template("Activación de cuenta de Chilan LRS", "Bienvenido a Chilan LRS", "Este es tu código de verificación de registro:", "Este código es válido durante 10 minutos. Si no fuiste tú, ignora este correo."),
        "vi": _auth_template("Kích hoạt tài khoản Chilan LRS", "Chào mừng đến với Chilan LRS", "Đây là mã xác minh đăng ký của bạn:", "Mã này có hiệu lực trong 10 phút. Nếu không phải bạn, hãy bỏ qua email này."),
        "pt": _auth_template("Ativação da conta Chilan LRS", "Bem-vindo ao Chilan LRS", "Aqui está o seu código de verificação de cadastro:", "Este código é válido por 10 minutos. Se não foi você, ignore este e-mail."),
        "ar": _auth_template("تفعيل حساب Chilan LRS", "مرحبًا بك في Chilan LRS", "إليك رمز التحقق الخاص بتسجيل الحساب:", "هذا الرمز صالح لمدة 10 دقائق. إذا لم تكن أنت، فتجاهل هذا البريد الإلكتروني."),
        "th": _auth_template("ยืนยันบัญชี Chilan LRS", "ยินดีต้อนรับสู่ Chilan LRS", "นี่คือรหัสยืนยันการสมัครของคุณ:", "รหัสนี้ใช้ได้ 10 นาที หากไม่ใช่คุณ กรุณาเพิกเฉยอีเมลนี้"),
        "ru": _auth_template("Активация аккаунта Chilan LRS", "Добро пожаловать в Chilan LRS", "Вот ваш код подтверждения регистрации:", "Код действителен 10 минут. Если это были не вы, проигнорируйте это письмо."),
        "id": _auth_template("Aktivasi akun Chilan LRS", "Selamat datang di Chilan LRS", "Berikut kode verifikasi pendaftaran Anda:", "Kode ini berlaku selama 10 menit. Jika ini bukan Anda, abaikan email ini."),
        "ms": _auth_template("Pengaktifan akaun Chilan LRS", "Selamat datang ke Chilan LRS", "Berikut ialah kod pengesahan pendaftaran anda:", "Kod ini sah selama 10 minit. Jika ini bukan anda, abaikan e-mel ini."),
        "it": _auth_template("Attivazione account Chilan LRS", "Benvenuto su Chilan LRS", "Ecco il tuo codice di verifica della registrazione:", "Questo codice è valido per 10 minuti. Se non sei stato tu, ignora questa email."),
    },
    "reset": {
        "zh": _auth_template("Chilan LRS 密码重置", "找回您的密码", "您正在尝试重置密码，验证码是：", "该验证码 10 分钟内有效。如果这不是您本人操作，请忽略此邮件。"),
        "en": _auth_template("Chilan LRS Password Reset", "Reset Password", "Your reset code is:", "This verification code is valid for 10 minutes. If you didn't request a reset, ignore this email."),
        "ja": _auth_template("Chilan LRS パスワード再設定", "パスワードを再設定", "パスワード再設定の確認コードはこちらです：", "この認証コードは10分間有効です。心当たりがない場合は、このメールを無視してください。"),
        "fr": _auth_template("Réinitialisation du mot de passe Chilan LRS", "Réinitialisez votre mot de passe", "Voici votre code de réinitialisation du mot de passe :", "Ce code de vérification est valable 10 minutes. Si vous n'avez pas demandé cette réinitialisation, ignorez cet e-mail."),
        "de": _auth_template("Chilan LRS Passwort zurücksetzen", "Setzen Sie Ihr Passwort zurück", "Hier ist Ihr Code zum Zurücksetzen des Passworts:", "Dieser Bestätigungscode ist 10 Minuten gültig. Wenn Sie dies nicht angefordert haben, ignorieren Sie diese E-Mail."),
        "ko": _auth_template("Chilan LRS 비밀번호 재설정", "비밀번호를 재설정하세요", "비밀번호 재설정 인증 코드는 다음과 같습니다:", "이 인증 코드는 10분 동안 유효합니다. 직접 요청한 것이 아니라면 이 메일을 무시하세요."),
        "es": _auth_template("Restablecimiento de contraseña de Chilan LRS", "Restablece tu contraseña", "Este es tu código para restablecer la contraseña:", "Este código de verificación es válido durante 10 minutos. Si no solicitaste este restablecimiento, ignora este correo."),
        "vi": _auth_template("Đặt lại mật khẩu Chilan LRS", "Đặt lại mật khẩu của bạn", "Đây là mã đặt lại mật khẩu của bạn:", "Mã xác minh này có hiệu lực trong 10 phút. Nếu bạn không yêu cầu thao tác này, hãy bỏ qua email này."),
        "pt": _auth_template("Redefinição de senha do Chilan LRS", "Redefina sua senha", "Aqui está o seu código para redefinir a senha:", "Este código de verificação é válido por 10 minutos. Se você não solicitou isso, ignore este e-mail."),
        "ar": _auth_template("إعادة تعيين كلمة مرور Chilan LRS", "أعد تعيين كلمة المرور", "إليك رمز إعادة تعيين كلمة المرور:", "رمز التحقق هذا صالح لمدة 10 دقائق. إذا لم تطلب هذا الإجراء، فتجاهل هذا البريد الإلكتروني."),
        "th": _auth_template("รีเซ็ตรหัสผ่าน Chilan LRS", "รีเซ็ตรหัสผ่านของคุณ", "นี่คือรหัสรีเซ็ตรหัสผ่านของคุณ:", "รหัสยืนยันนี้ใช้ได้ 10 นาที หากคุณไม่ได้ร้องขอรายการนี้ กรุณาเพิกเฉยอีเมลนี้"),
        "ru": _auth_template("Сброс пароля Chilan LRS", "Сбросьте пароль", "Вот ваш код для сброса пароля:", "Этот код подтверждения действителен 10 минут. Если вы не запрашивали сброс, проигнорируйте это письмо."),
        "id": _auth_template("Atur ulang kata sandi Chilan LRS", "Atur ulang kata sandi Anda", "Berikut kode untuk mengatur ulang kata sandi Anda:", "Kode verifikasi ini berlaku selama 10 menit. Jika Anda tidak meminta ini, abaikan email ini."),
        "ms": _auth_template("Tetapkan semula kata laluan Chilan LRS", "Tetapkan semula kata laluan anda", "Berikut ialah kod tetapan semula kata laluan anda:", "Kod pengesahan ini sah selama 10 minit. Jika anda tidak meminta tindakan ini, abaikan e-mel ini."),
        "it": _auth_template("Reimpostazione password Chilan LRS", "Reimposta la tua password", "Ecco il tuo codice per reimpostare la password:", "Questo codice di verifica è valido per 10 minuti. Se non hai richiesto questa operazione, ignora questa email."),
    },
    "unusual_login": {
        "zh": _auth_template("Chilan LRS 登录安全提醒", "检测到新的登录环境", "你的账号刚刚在新的设备和网络环境中完成登录。", "如果这是你本人操作，无需进一步处理；如果不是，请尽快修改密码并检查最近登录记录。"),
        "en": _auth_template("Chilan LRS Sign-in Security Alert", "We noticed a new sign-in environment", "Your account just signed in from a new device and network environment.", "If this was you, no action is needed. If not, please reset your password and review recent sign-ins."),
        "ja": _auth_template("Chilan LRS ログインセキュリティ通知", "新しいログイン環境を検出しました", "新しい端末とネットワーク環境からアカウントへのログインがありました。", "ご自身の操作であれば対応不要です。心当たりがない場合は、すぐにパスワードを変更し最近のログイン履歴をご確認ください。"),
        "fr": _auth_template("Alerte de sécurité de connexion Chilan LRS", "Nous avons détecté un nouvel environnement de connexion", "Votre compte vient d'être connecté depuis un nouvel appareil et un nouveau réseau.", "Si c'était bien vous, aucune action n'est nécessaire. Sinon, réinitialisez immédiatement votre mot de passe et vérifiez vos connexions récentes."),
        "de": _auth_template("Chilan LRS Sicherheitswarnung zur Anmeldung", "Wir haben eine neue Anmeldeumgebung erkannt", "Ihr Konto wurde gerade von einem neuen Gerät und Netzwerk aus verwendet.", "Wenn Sie das waren, ist keine weitere Aktion nötig. Wenn nicht, setzen Sie Ihr Passwort bitte sofort zurück und prüfen Sie Ihre letzten Anmeldungen."),
        "ko": _auth_template("Chilan LRS 로그인 보안 알림", "새로운 로그인 환경이 감지되었습니다", "새로운 기기와 네트워크 환경에서 계정 로그인 시도가 있었습니다.", "본인 로그인이라면 추가 조치가 필요하지 않습니다. 아니라면 즉시 비밀번호를 재설정하고 최근 로그인 기록을 확인하세요."),
        "es": _auth_template("Alerta de seguridad de inicio de sesión de Chilan LRS", "Detectamos un nuevo entorno de inicio de sesión", "Tu cuenta acaba de iniciar sesión desde un dispositivo y una red nuevos.", "Si fuiste tú, no necesitas hacer nada. Si no, restablece tu contraseña de inmediato y revisa tus inicios de sesión recientes."),
        "vi": _auth_template("Cảnh báo bảo mật đăng nhập Chilan LRS", "Chúng tôi phát hiện một môi trường đăng nhập mới", "Tài khoản của bạn vừa đăng nhập từ một thiết bị và mạng mới.", "Nếu đó là bạn, bạn không cần làm gì thêm. Nếu không, hãy đặt lại mật khẩu ngay và kiểm tra các lần đăng nhập gần đây."),
        "pt": _auth_template("Alerta de segurança de login do Chilan LRS", "Detectamos um novo ambiente de login", "Sua conta acabou de entrar a partir de um novo dispositivo e rede.", "Se foi você, nenhuma ação é necessária. Caso contrário, redefina sua senha imediatamente e revise seus acessos recentes."),
        "ar": _auth_template("تنبيه أمان تسجيل الدخول في Chilan LRS", "اكتشفنا بيئة تسجيل دخول جديدة", "تم تسجيل الدخول إلى حسابك من جهاز وشبكة جديدين.", "إذا كنت أنت، فلا يلزم أي إجراء. وإذا لم تكن أنت، فأعد تعيين كلمة المرور فورًا وراجع عمليات تسجيل الدخول الأخيرة."),
        "th": _auth_template("การแจ้งเตือนความปลอดภัยการเข้าสู่ระบบ Chilan LRS", "ตรวจพบสภาพแวดล้อมการเข้าสู่ระบบใหม่", "บัญชีของคุณเพิ่งเข้าสู่ระบบจากอุปกรณ์และเครือข่ายใหม่", "หากเป็นคุณเอง ไม่จำเป็นต้องดำเนินการเพิ่มเติม หากไม่ใช่ กรุณารีเซ็ตรหัสผ่านทันทีและตรวจสอบประวัติการเข้าสู่ระบบล่าสุด"),
        "ru": _auth_template("Предупреждение о безопасности входа Chilan LRS", "Мы обнаружили новую среду входа", "В ваш аккаунт только что вошли с нового устройства и из новой сети.", "Если это были вы, никаких действий не требуется. Если нет, немедленно смените пароль и проверьте последние входы."),
        "id": _auth_template("Peringatan keamanan login Chilan LRS", "Kami mendeteksi lingkungan login baru", "Akun Anda baru saja masuk dari perangkat dan jaringan baru.", "Jika ini Anda, tidak ada tindakan lebih lanjut yang diperlukan. Jika bukan, segera atur ulang kata sandi Anda dan periksa login terbaru."),
        "ms": _auth_template("Amaran keselamatan log masuk Chilan LRS", "Kami mengesan persekitaran log masuk baharu", "Akaun anda baru sahaja log masuk daripada peranti dan rangkaian baharu.", "Jika ini anda, tiada tindakan lanjut diperlukan. Jika bukan, tetapkan semula kata laluan anda dengan segera dan semak log masuk terkini."),
        "it": _auth_template("Avviso di sicurezza accesso Chilan LRS", "Abbiamo rilevato un nuovo ambiente di accesso", "Il tuo account ha appena effettuato l'accesso da un nuovo dispositivo e da una nuova rete.", "Se sei stato tu, non è necessaria alcuna azione. In caso contrario, reimposta subito la password e controlla gli accessi recenti."),
    },
    "password_changed_success": {
        "zh": _auth_template("Chilan LRS 密码已更新", "你的密码已成功更新", "你的 Chilan LRS 账号密码刚刚被成功修改。", "如果这不是你本人操作，请立即重置密码并检查最近登录记录。"),
        "en": _auth_template("Chilan LRS Password Updated", "Your password was changed successfully", "Your Chilan LRS account password was just updated successfully.", "If this wasn't you, reset your password immediately and review recent sign-ins."),
        "ja": _auth_template("Chilan LRS パスワード更新完了", "パスワードが正常に更新されました", "Chilan LRS アカウントのパスワードが更新されました。", "心当たりがない場合は、すぐにパスワードを再設定し最近のログイン履歴をご確認ください。"),
        "fr": _auth_template("Mot de passe Chilan LRS mis à jour", "Votre mot de passe a bien été mis à jour", "Le mot de passe de votre compte Chilan LRS vient d'être modifié avec succès.", "Si ce n'était pas vous, réinitialisez immédiatement votre mot de passe et vérifiez vos connexions récentes."),
        "de": _auth_template("Chilan LRS Passwort aktualisiert", "Ihr Passwort wurde erfolgreich geändert", "Das Passwort Ihres Chilan LRS Kontos wurde soeben erfolgreich aktualisiert.", "Wenn Sie das nicht waren, setzen Sie Ihr Passwort sofort zurück und prüfen Sie Ihre letzten Anmeldungen."),
        "ko": _auth_template("Chilan LRS 비밀번호가 업데이트되었습니다", "비밀번호가 성공적으로 변경되었습니다", "Chilan LRS 계정 비밀번호가 방금 성공적으로 변경되었습니다.", "본인이 아니라면 즉시 비밀번호를 재설정하고 최근 로그인 기록을 확인하세요."),
        "es": _auth_template("Contraseña de Chilan LRS actualizada", "Tu contraseña se actualizó correctamente", "La contraseña de tu cuenta de Chilan LRS acaba de actualizarse correctamente.", "Si no fuiste tú, restablece tu contraseña de inmediato y revisa tus inicios de sesión recientes."),
        "vi": _auth_template("Mật khẩu Chilan LRS đã được cập nhật", "Mật khẩu của bạn đã được cập nhật thành công", "Mật khẩu tài khoản Chilan LRS của bạn vừa được cập nhật thành công.", "Nếu đó không phải là bạn, hãy đặt lại mật khẩu ngay và kiểm tra các lần đăng nhập gần đây."),
        "pt": _auth_template("Senha do Chilan LRS atualizada", "Sua senha foi atualizada com sucesso", "A senha da sua conta Chilan LRS acabou de ser atualizada com sucesso.", "Se não foi você, redefina sua senha imediatamente e revise seus acessos recentes."),
        "ar": _auth_template("تم تحديث كلمة مرور Chilan LRS", "تم تغيير كلمة المرور بنجاح", "تم تحديث كلمة مرور حسابك في Chilan LRS بنجاح.", "إذا لم تكن أنت، فأعد تعيين كلمة المرور فورًا وراجع عمليات تسجيل الدخول الأخيرة."),
        "th": _auth_template("อัปเดตรหัสผ่าน Chilan LRS แล้ว", "รหัสผ่านของคุณถูกอัปเดตเรียบร้อยแล้ว", "รหัสผ่านบัญชี Chilan LRS ของคุณเพิ่งถูกอัปเดตสำเร็จ", "หากไม่ใช่คุณ กรุณารีเซ็ตรหัสผ่านทันทีและตรวจสอบประวัติการเข้าสู่ระบบล่าสุด"),
        "ru": _auth_template("Пароль Chilan LRS обновлён", "Ваш пароль успешно изменён", "Пароль вашего аккаунта Chilan LRS только что был успешно обновлён.", "Если это были не вы, немедленно смените пароль и проверьте последние входы."),
        "id": _auth_template("Kata sandi Chilan LRS diperbarui", "Kata sandi Anda berhasil diperbarui", "Kata sandi akun Chilan LRS Anda baru saja berhasil diperbarui.", "Jika ini bukan Anda, segera atur ulang kata sandi Anda dan periksa login terbaru."),
        "ms": _auth_template("Kata laluan Chilan LRS dikemas kini", "Kata laluan anda berjaya dikemas kini", "Kata laluan akaun Chilan LRS anda baru sahaja berjaya dikemas kini.", "Jika ini bukan anda, tetapkan semula kata laluan anda dengan segera dan semak log masuk terkini."),
        "it": _auth_template("Password Chilan LRS aggiornata", "La tua password è stata aggiornata con successo", "La password del tuo account Chilan LRS è stata appena aggiornata con successo.", "Se non sei stato tu, reimposta immediatamente la password e controlla gli accessi recenti."),
    },
}

AUTH_SUPPORTED_EMAIL_LANGS = set(AUTH_EMAIL_TEMPLATES["signup"].keys())
AUTH_EMAIL_LANG_ALIASES = {
    "jp": "ja",
    "ja": "ja",
    "ja-jp": "ja",
    "zh": "zh",
    "zh-cn": "zh",
    "zh-hans": "zh",
    "zh-hans-cn": "zh",
    "zh-hant": "zh",
    "zh-hk": "zh",
    "zh-tw": "zh",
    "en": "en",
    "en-us": "en",
    "en-gb": "en",
}

AUTH_EMAIL_COPY = {
    "zh": {
        "login_method": "登录方式",
        "device": "设备",
        "ip": "IP",
        "time": "时间",
        "change_source": "变更方式",
        "unknown": "未知",
        "unknown_device": "未知设备",
        "unusual_login_highlight": "新登录提醒",
        "password_changed_highlight": "密码更新成功",
        "provider_password": "邮箱密码",
        "change_source_reset": "通过邮箱验证码重置",
        "change_source_change": "在账号设置中修改",
    },
    "en": {
        "login_method": "Sign-in method",
        "device": "Device",
        "ip": "IP",
        "time": "Time",
        "change_source": "Change source",
        "unknown": "Unknown",
        "unknown_device": "Unknown device",
        "unusual_login_highlight": "New sign-in detected",
        "password_changed_highlight": "Password updated",
        "provider_password": "Email & Password",
        "change_source_reset": "Reset via email verification",
        "change_source_change": "Changed from account settings",
    },
    "ja": {
        "login_method": "ログイン方法",
        "device": "デバイス",
        "ip": "IP",
        "time": "時刻",
        "change_source": "変更方法",
        "unknown": "不明",
        "unknown_device": "不明なデバイス",
        "unusual_login_highlight": "新しいログインを検出",
        "password_changed_highlight": "パスワード更新完了",
        "provider_password": "メールとパスワード",
        "change_source_reset": "メール認証コードで再設定",
        "change_source_change": "アカウント設定から変更",
    },
}


def normalize_auth_email_lang(raw_lang: str | None) -> str | None:
    if raw_lang is None:
        return None
    normalized = str(raw_lang).strip().lower().replace("_", "-")
    if not normalized:
        return None
    normalized = normalized.split(",", 1)[0].split(";", 1)[0].strip()
    normalized = AUTH_EMAIL_LANG_ALIASES.get(normalized, normalized)
    primary = normalized.split("-", 1)[0].strip()
    primary = AUTH_EMAIL_LANG_ALIASES.get(primary, primary)
    if primary in AUTH_SUPPORTED_EMAIL_LANGS:
        return primary
    return None


def resolve_auth_email_lang(request: Request | None = None, explicit_lang: str | None = None, fallback: str = AUTH_EMAIL_DEFAULT_LANG) -> str:
    candidates = []
    if request is not None:
        candidates.append((request.headers.get(INTERFACE_LANGUAGE_HEADER), True))
    candidates.append((explicit_lang, True))
    if request is not None:
        candidates.append((request.headers.get("accept-language"), False))

    for raw_value, explicit in candidates:
        raw_text = str(raw_value or "").strip()
        if not raw_text:
            continue
        normalized = normalize_auth_email_lang(raw_text)
        if normalized:
            return normalized
        if explicit:
            return AUTH_EMAIL_UNSUPPORTED_FALLBACK_LANG
    return fallback


def infer_mail_lang_from_request(request: Request | None, fallback: str = AUTH_EMAIL_DEFAULT_LANG) -> str:
    return resolve_auth_email_lang(request=request, fallback=fallback)


def _get_auth_email_copy(lang: str) -> dict:
    normalized = normalize_auth_email_lang(lang) or AUTH_EMAIL_UNSUPPORTED_FALLBACK_LANG
    if normalized == "zh":
        return AUTH_EMAIL_COPY["zh"]
    if normalized == "ja":
        return AUTH_EMAIL_COPY["ja"]
    return AUTH_EMAIL_COPY[AUTH_EMAIL_UNSUPPORTED_FALLBACK_LANG]


def _now_utc_label() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _translate_login_provider(provider: str, lang: str) -> str:
    normalized = (provider or "password").strip().lower()
    copy = _get_auth_email_copy(lang)
    mapping = {
        "password": copy["provider_password"],
        "google": "Google",
        "apple": "Apple",
    }
    return mapping.get(normalized, normalized or copy["unknown"])


def _translate_password_change_source(change_source: str, lang: str) -> str:
    normalized = (change_source or "change").strip().lower()
    copy = _get_auth_email_copy(lang)
    mapping = {
        "reset": copy["change_source_reset"],
        "change": copy["change_source_change"],
    }
    return mapping.get(normalized, copy["change_source_change"])


def _display_device_info(device_info: str | None, lang: str) -> str:
    copy = _get_auth_email_copy(lang)
    value = (device_info or "").strip()
    if not value or value == "Unknown device":
        return copy["unknown_device"]
    return value


def _display_value(value: str | None, lang: str) -> str:
    copy = _get_auth_email_copy(lang)
    normalized = (value or "").strip()
    return normalized or copy["unknown"]


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
    lang: str = AUTH_EMAIL_DEFAULT_LANG,
    details=None,
    highlight_is_code: bool | None = None,
):
    lang_key = normalize_auth_email_lang(lang) or AUTH_EMAIL_UNSUPPORTED_FALLBACK_LANG
    template_group = AUTH_EMAIL_TEMPLATES.get(email_type)
    if not template_group:
        raise ValueError(f"Unsupported auth email type: {email_type}")
    template = template_group.get(lang_key) or template_group.get(AUTH_EMAIL_UNSUPPORTED_FALLBACK_LANG)
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
        _send_email_via_resend(to_email, template["subject"], content)
    else:
        _send_email_via_smtp(to_email, template["subject"], content)


def try_send_auth_email(*args, **kwargs):
    try:
        send_auth_email(*args, **kwargs)
    except Exception as e:
        email_type = kwargs.get("email_type") or (args[2] if len(args) > 2 else "unknown")
        print(
            f"[auth-mail] non-blocking send failed "
            f"type={email_type} error={type(e).__name__}: {e}"
        )


def try_send_unusual_login_email(to_email: str, provider: str, login_context: dict, lang: str = AUTH_EMAIL_DEFAULT_LANG):
    copy = _get_auth_email_copy(lang)
    details = [
        (copy["login_method"], _translate_login_provider(provider, lang)),
        (copy["device"], _display_device_info(login_context.get("device_info"), lang)),
        (copy["ip"], _display_value(login_context.get("ip_address"), lang)),
        (copy["time"], _now_utc_label()),
    ]
    highlight_value = _display_device_info(login_context.get("device_info"), lang)
    if highlight_value == copy["unknown_device"]:
        highlight_value = copy["unusual_login_highlight"]

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
    lang: str = AUTH_EMAIL_DEFAULT_LANG,
    change_source: str = "change",
    login_context: dict | None = None,
):
    login_context = login_context or {}
    copy = _get_auth_email_copy(lang)
    details = [
        (copy["change_source"], _translate_password_change_source(change_source, lang)),
        (copy["time"], _now_utc_label()),
    ]
    if login_context.get("device_info"):
        details.append((copy["device"], _display_device_info(login_context.get("device_info"), lang)))
    if login_context.get("ip_address"):
        details.append((copy["ip"], _display_value(login_context.get("ip_address"), lang)))

    try_send_auth_email(
        to_email,
        copy["password_changed_highlight"],
        email_type="password_changed_success",
        lang=lang,
        details=details,
        highlight_is_code=False,
    )


@router.post("/signup")
async def signup(req: SignupReq, request: Request, db=Depends(get_db)):
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
    send_auth_email(req.email, code, "signup", resolve_auth_email_lang(request=request, explicit_lang=req.lang))
    db.commit()
    return {"status": "success"}


@router.post("/verify")
async def verify(req: VerifyReq, request: Request, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT code, created_at FROM verification_codes WHERE email = %s", (req.email,))
    row = cur.fetchone()
    _raise_if_verification_code_invalid(db, req.email, row, req.code, resolve_auth_email_lang(request=request))
    cur.execute("UPDATE users SET is_active = TRUE WHERE email = %s", (req.email,))
    _delete_verification_code(db, req.email)
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
            lang=resolve_auth_email_lang(request=request),
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
    send_auth_email(req.email, code, "reset", resolve_auth_email_lang(request=request))
    db.commit()
    return {"status": "success"}


@router.post("/reset-password")
async def reset_password(req: ResetReq, request: Request, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT code, created_at FROM verification_codes WHERE email = %s", (req.email,))
    row = cur.fetchone()
    _raise_if_verification_code_invalid(db, req.email, row, req.code, resolve_auth_email_lang(request=request))
    cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", (get_password_hash(req.new_password), req.email))
    _delete_verification_code(db, req.email)
    db.commit()
    try_send_password_changed_email(
        req.email,
        lang=resolve_auth_email_lang(request=request),
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
            lang=resolve_auth_email_lang(request=request),
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
                lang=resolve_auth_email_lang(request=request),
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
