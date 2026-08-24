import mimetypes
from pathlib import Path
from urllib.parse import quote
from config.env import get_env, get_env_int

try:
    import boto3
    from botocore.config import Config as BotocoreConfig
except ImportError:
    boto3 = None
    BotocoreConfig = None


class R2Storage:
    """
    Cloudflare R2 媒体存储（S3 兼容接口，使用 boto3）。

    COS 路径约定：
      zh/audio/{lesson_folder}/sentences/{file}   ← 中文逐句音频
      zh/audio/{lesson_folder}/full/{file}        ← 中文完整对话音频
      zh/video/{learner_lang}/{file}              ← 讲解视频（按学习者母语区分）
    """

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket: str,
        public_base_url: str = "",
        signed_url_expires_seconds: int = 3600,
    ):
        self.account_id = account_id.strip()
        self.access_key_id = access_key_id.strip()
        self.secret_access_key = secret_access_key.strip()
        self.bucket = bucket.strip()
        self.public_base_url = (public_base_url or "").strip().rstrip("/")
        self.signed_url_expires_seconds = int(signed_url_expires_seconds)
        self._endpoint = f"https://{self.account_id}.r2.cloudflarestorage.com"
        self._client = None

    @classmethod
    def from_env(cls, optional: bool = False):
        account_id = get_env("STORAGE_R2_ACCOUNT_ID", default="")
        access_key_id = get_env("STORAGE_R2_ACCESS_KEY_ID", default="")
        secret_access_key = get_env("STORAGE_R2_SECRET_ACCESS_KEY", default="")
        bucket = get_env("STORAGE_R2_BUCKET", default="")

        if not all([account_id, access_key_id, secret_access_key, bucket]):
            if optional:
                return None
            raise ValueError("STORAGE_R2_* 环境变量未完整配置。")

        return cls(
            account_id=account_id,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            bucket=bucket,
            public_base_url=get_env("STORAGE_R2_PUBLIC_BASE_URL", default=""),
            signed_url_expires_seconds=get_env_int(
                "STORAGE_R2_SIGNED_URL_EXPIRES_SECONDS", default=3600
            ),
        )

    def _require_sdk(self):
        if boto3 is None:
            raise RuntimeError("未安装 boto3，请执行 pip install boto3。")

    def _get_client(self):
        self._require_sdk()
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self._endpoint,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name="auto",
                config=BotocoreConfig(signature_version="s3v4"),
            )
        return self._client

    def _normalize_key(self, object_key: str) -> str:
        return (object_key or "").strip().lstrip("/")

    def _guess_content_type(self, local_path: str | Path, explicit: str | None = None) -> str:
        if explicit:
            return explicit
        guessed, _ = mimetypes.guess_type(str(local_path))
        return guessed or "application/octet-stream"

    def build_public_url(self, object_key: str) -> str:
        normalized_key = self._normalize_key(object_key)
        if self.public_base_url:
            return f"{self.public_base_url}/{quote(normalized_key)}"
        return f"{self._endpoint}/{self.bucket}/{quote(normalized_key)}"

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

        with path.open("rb") as f:
            client.put_object(
                Bucket=self.bucket,
                Key=normalized_key,
                Body=f,
                ContentType=resolved_content_type,
            )

        return {
            "bucket": self.bucket,
            "object_key": normalized_key,
            "content_type": resolved_content_type,
            "public_url": self.build_public_url(normalized_key),
        }

    def resolve_url(self, object_key: str, expires_seconds: int | None = None) -> str:
        normalized_key = self._normalize_key(object_key)
        if not normalized_key:
            return ""

        if self.public_base_url:
            return self.build_public_url(normalized_key)

        client = self._get_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": normalized_key},
            ExpiresIn=expires_seconds or self.signed_url_expires_seconds,
        )

    def get_object_metadata(self, object_key: str) -> dict:
        normalized_key = self._normalize_key(object_key)
        if not normalized_key:
            raise ValueError("object_key cannot be empty")
        response = self._get_client().head_object(Bucket=self.bucket, Key=normalized_key)
        return {
            "object_key": normalized_key,
            "content_length": int(response.get("ContentLength") or 0),
            "content_type": response.get("ContentType") or "",
            "etag": str(response.get("ETag") or "").strip('"'),
        }

    def delete_object(self, object_key: str) -> bool:
        normalized_key = self._normalize_key(object_key)
        if not normalized_key:
            return False
        client = self._get_client()
        client.delete_object(Bucket=self.bucket, Key=normalized_key)
        return True
