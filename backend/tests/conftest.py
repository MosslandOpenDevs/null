import pytest

from null_engine.config import settings


@pytest.fixture(autouse=True)
def _allow_anonymous_writes():
    """The API smoke tests exercise dev-mode behavior (no write token).

    Write protection itself is covered by tests/test_write_auth.py.
    """
    original_token = settings.api_write_token
    original_anon = settings.allow_anonymous_writes
    settings.api_write_token = ""
    settings.allow_anonymous_writes = True
    yield
    settings.api_write_token = original_token
    settings.allow_anonymous_writes = original_anon
