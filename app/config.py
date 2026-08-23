from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).resolve().parent.parent
_DB_PATH = (_BASE_DIR / "tea_shop.db").as_posix()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    super_admin_id: int
    channel_id: int
    database_url: str = f"sqlite+aiosqlite:///{_DB_PATH}"
    webapp_url: str = ""
    webapp_host: str = "0.0.0.0"
    webapp_port: int = 8000
    webapp_serve: bool = True
    webapp_debug: bool = False

    @property
    def public_webapp_url(self) -> str | None:
        raw = self.webapp_url.strip()
        if not raw:
            return None
        lowered = raw.lower()
        if not lowered.startswith("https://"):
            return None
        host = lowered.removeprefix("https://").split("/", 1)[0]
        if host in {"yourdomain.com", "www.yourdomain.com"}:
            return None
        if not raw.endswith("/"):
            return f"{raw}/"
        return raw


settings = Settings()
