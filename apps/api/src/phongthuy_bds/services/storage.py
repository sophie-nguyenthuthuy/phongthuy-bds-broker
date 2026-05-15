"""Storage abstraction — local FS cho dev, S3-compatible cho prod."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from phongthuy_bds.core.config import get_settings
from phongthuy_bds.core.logging import get_logger

log = get_logger(__name__)


class Storage(Protocol):
    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...
    def url_for(self, key: str, expires_in: int = 3600) -> str: ...


class LocalStorage:
    def __init__(self, base_path: str) -> None:
        self.base = Path(base_path).resolve()
        self.base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Guard against path traversal.
        p = (self.base / key).resolve()
        if not str(p).startswith(str(self.base)):
            raise ValueError(f"Bad key {key!r}: tries to escape storage root")
        return p

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        log.debug("storage.local.put", key=key, size=len(data))
        return key

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        p = self._path(key)
        if p.exists():
            p.unlink()

    def url_for(self, key: str, expires_in: int = 3600) -> str:
        # In dev, the API serves files via /v1/storage/{key} (mounted route).
        return f"/v1/storage/{key}"


class S3Storage:
    def __init__(
        self,
        endpoint_url: str,
        bucket: str,
        access_key: str,
        secret_key: str,
    ) -> None:
        import boto3  # type: ignore[import-not-found]
        self.bucket = bucket
        self.s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return key

    def get(self, key: str) -> bytes:
        obj = self.s3.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()  # type: ignore[no-any-return]

    def delete(self, key: str) -> None:
        self.s3.delete_object(Bucket=self.bucket, Key=key)

    def url_for(self, key: str, expires_in: int = 3600) -> str:
        return self.s3.generate_presigned_url(  # type: ignore[no-any-return]
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )


def get_storage() -> Storage:
    settings = get_settings()
    if settings.storage_backend == "local":
        return LocalStorage(settings.storage_local_path)
    if settings.storage_backend == "s3":
        if not (settings.s3_endpoint_url and settings.s3_bucket
                and settings.s3_access_key and settings.s3_secret_key):
            raise RuntimeError("Storage backend=s3 nhưng thiếu credential")
        return S3Storage(
            endpoint_url=settings.s3_endpoint_url,
            bucket=settings.s3_bucket,
            access_key=settings.s3_access_key.get_secret_value(),
            secret_key=settings.s3_secret_key.get_secret_value(),
        )
    raise RuntimeError(f"Storage backend không hỗ trợ: {settings.storage_backend}")
