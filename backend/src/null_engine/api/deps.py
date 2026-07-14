"""Shared API dependencies."""

import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from null_engine.config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_write_access(api_key: str | None = Security(_api_key_header)) -> None:
    """Guard state-mutating endpoints.

    - If ``api_write_token`` is configured, the request must present it in
      the ``X-API-Key`` header.
    - Otherwise writes are only allowed when ``allow_anonymous_writes`` is
      explicitly enabled (local development).
    """
    if settings.api_write_token:
        if api_key and secrets.compare_digest(api_key, settings.api_write_token):
            return
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    if settings.allow_anonymous_writes:
        return
    raise HTTPException(
        status_code=403,
        detail="Write access is disabled. Configure API_WRITE_TOKEN or enable ALLOW_ANONYMOUS_WRITES.",
    )
