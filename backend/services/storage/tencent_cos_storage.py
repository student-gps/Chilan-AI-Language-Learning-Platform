import mimetypes
import os
from pathlib import Path
from urllib.parse import quote
from config.env import get_env, get_env_bool, get_env_int

try:
    from qcloud_cos import CosConfig, CosS3Client
except ImportError:  # pragma: no cover - runtime dependency
    CosConfig = None
    CosS3Client = None


class TencentCOSStorage:
    def __init__(
        self,
        secret_id: str,
        secret_key: str,
        region: str,
        bucket: str,
        public_base_url: str = "",
        use_signed_url: bool = True,
        signed_url_expires_seconds: int = 3600,
        scheme: str = "https",
    ):
        self.secret_id = (secret_id or "").strip()
        self.secret_key = (secret_key or "").strip()
        self.region = (region or "").strip()
        self.bucket = (bucket or "").strip()
        self.public_base_url = (public_base_url or "").strip().rstrip("/")
        self.use_signed_url = bool(use_signed_url)
        self.signed_url_expires_seconds = int(signed_url_expires_seconds)
        self.scheme = scheme
        self._client = None

    @classmethod
    def from_env(cls, optional: bool = False):
        secret_id = get_env("STORAGE_COS_SECRET_ID", "TENCENT_COS_SECRET_ID", default="")
        secret_key = get_env("STORAGE_COS_SECRET_KEY", "TENCENT_COS_SECRET_KEY", default="")
        region = get_env("STORAGE_COS_REGION", "TENCENT_COS_REGION", default="")
        bucket = get_env("STORAGE_COS_BUCKET", "TENCENT_COS_BUCKET", default="")

        if not all([secret_id, secret_key, region, bucket]):
            if optional:
                return None
            raise ValueError("TENCENT_COS_* 环境变量未完整配置。")

        return cls(
            secret_id=secret_id,
            secret_key=secret_key,
            region=region,
            bucket=bucket,
            public_base_url=get_env("STORAGE_COS_PUBLIC_BASE_URL", "TENCENT_COS_PUBLIC_BASE_URL", default=""),
            use_signed_url=get_env_bool("STORAGE_COS_USE_SIGNED_URL", "TENCENT_COS_USE_SIGNED_URL", default=True),
            signed_url_expires_seconds=get_env_int(
                "STORAGE_COS_SIGNED_URL_EXPIRES_SECONDS",
                "TENCENT_COS_SIGNED_URL_EXPIRES_SECONDS",
                default=3600,
            ),
        )

    def _require_sdk(self):
        if CosConfig is None or CosS3Client is None:
            raise RuntimeError(
                "未安装腾讯云 COS SDK，请在 backend/requirements.txt 中安装 cos-python-sdk-v5。"
            )

    def _get_client(self):
        self._require_sdk()
        if self._client is None:
            config = CosConfig(
                Region=self.region,
                SecretId=self.secret_id,
                SecretKey=self.secret_key,
                Scheme=self.scheme,
            )
            self._client = CosS3Client(config)
        return self._client

    def _normalize_key(self, object_key: str) -> str:
        return (object_key or "").strip().lstrip("/")

    def _guess_content_type(self, local_path: str | Path, explicit_content_type: str | None = None) -> str:
        if explicit_content_type:
            return explicit_content_type
        guessed, _ = mimetypes.guess_type(str(local_path))
        return guessed or "application/octet-stream"

    def build_public_url(self, object_key: str) -> str:
        normalized_key = self._normalize_key(object_key)
        if self.public_base_url:
            return f"{self.public_base_url}/{quote(normalized_key)}"
        return f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{quote(normalized_key)}"

    def upload_file(
        self,
        local_path: str | Path,
        object_key: str,
        content_type: str | None = None,
    ) -> dict:
        client = self._get_client()
        path = Path(local_path)
        normalized_key = self._normalize_key(object_key)
        resolved_content_type = self._guess_content_type(path, content_type)

        with path.open("rb") as file_obj:
            response = client.put_object(
                Bucket=self.bucket,
                Body=file_obj,
                Key=normalized_key,
                EnableMD5=False,
                ContentType=resolved_content_type,
            )

        return {
            "bucket": self.bucket,
            "region": self.region,
            "object_key": normalized_key,
            "etag": response.get("ETag", "") if isinstance(response, dict) else "",
            "content_type": resolved_content_type,
            "public_url": self.build_public_url(normalized_key),
        }

    def resolve_url(self, object_key: str, expires_seconds: int | None = None) -> str:
        normalized_key = self._normalize_key(object_key)
        if not normalized_key:
            return ""

        if self.public_base_url and not self.use_signed_url:
            return self.build_public_url(normalized_key)

        if self.public_base_url and self.use_signed_url:
            # 自定义公有域名场景下直接返回固定 URL，后续如接 CDN 鉴权可再升级
            return self.build_public_url(normalized_key)

        if not self.use_signed_url:
            return self.build_public_url(normalized_key)

        client = self._get_client()
        return client.get_presigned_url(
            Method="GET",
            Bucket=self.bucket,
            Key=normalized_key,
            Expired=expires_seconds or self.signed_url_expires_seconds,
        )

    def delete_object(self, object_key: str) -> bool:
        normalized_key = self._normalize_key(object_key)
        if not normalized_key:
            return False

        client = self._get_client()
        client.delete_object(Bucket=self.bucket, Key=normalized_key)
        return True
