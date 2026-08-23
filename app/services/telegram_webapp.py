import hashlib
import hmac
import json
from dataclasses import dataclass
from time import time
from urllib.parse import parse_qsl, unquote

_MAX_AUTH_AGE_SECONDS = 86_400


class InvalidWebAppDataError(Exception):
    def __init__(self, reason: str = "invalid") -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class WebAppUser:
    id: int
    username: str | None
    first_name: str | None


def normalize_init_data(raw: str) -> str:
    stripped = raw.strip()
    if not stripped:
        return ""
    if stripped.lower().startswith("tma "):
        stripped = stripped[4:].strip()
    if "hash=" in stripped:
        return stripped
    decoded = unquote(stripped)
    if "hash=" in decoded:
        return decoded
    return stripped


def parse_webapp_user(init_data: str, bot_token: str) -> WebAppUser:
    payload = normalize_init_data(init_data)
    if not payload:
        raise InvalidWebAppDataError("empty")
    try:
        parsed = dict(parse_qsl(payload, keep_blank_values=True))
    except ValueError as error:
        raise InvalidWebAppDataError("malformed") from error
    received_hash = parsed.pop("hash", "")
    if not received_hash:
        raise InvalidWebAppDataError("missing_hash")
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hash, received_hash):
        raise InvalidWebAppDataError("bad_hash")
    auth_date_raw = parsed.get("auth_date", "")
    try:
        auth_date = int(auth_date_raw)
    except ValueError as error:
        raise InvalidWebAppDataError("bad_auth_date") from error
    if auth_date > 0 and time() - auth_date > _MAX_AUTH_AGE_SECONDS:
        raise InvalidWebAppDataError("expired")
    user_raw = parsed.get("user")
    if not user_raw:
        raise InvalidWebAppDataError("missing_user")
    try:
        user_payload = json.loads(user_raw)
        telegram_id = int(user_payload["id"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise InvalidWebAppDataError("bad_user") from error
    username = user_payload.get("username")
    first_name = user_payload.get("first_name")
    return WebAppUser(
        id=telegram_id,
        username=username if isinstance(username, str) else None,
        first_name=first_name if isinstance(first_name, str) else None,
    )
