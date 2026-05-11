from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    bot_token: str
    admin_ids: list[int] = Field(default_factory=list)
    support_username: str = "@support"
    bot_username: str = "vpn_bot"

    database_url: str
    redis_url: str = "redis://redis:6379/0"

    remnawave_api_url: str = "https://panel.example.com"
    remnawave_api_token: str = ""
    remnawave_default_squad_uuid: str = ""

    webhook_base_url: str = "https://bot.example.com"
    webhook_secret: str = "change_me"

    cryptomus_merchant_uuid: str = ""
    cryptomus_api_key: str = ""
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""
    paypalych_api_url: str = "https://pally.info/api/v1"
    paypalych_api_token: str = ""
    paypalych_shop_id: str = ""

    payments_fake_enabled: bool = True

    trial_days: int = 3
    trial_traffic_gb: int = 10
    referral_percent: int = 20

    log_level: str = "INFO"
    tz: str = "Europe/Moscow"

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    @property
    def admin_ids_set(self) -> set[int]:
        return set(self.admin_ids)

    @property
    def available_payment_methods(self) -> list[str]:
        methods: list[str] = []
        if self.payments_fake_enabled:
            methods.append("fake")
        methods.append("stars")
        if self.paypalych_api_token and self.paypalych_shop_id:
            methods.append("paypalych")
        if self.yookassa_shop_id and self.yookassa_secret_key:
            methods.append("yookassa")
        if self.cryptomus_merchant_uuid and self.cryptomus_api_key:
            methods.append("cryptomus")
        return methods

    @property
    def remnawave_configured(self) -> bool:
        return bool(self.remnawave_api_token and self.remnawave_default_squad_uuid)


@lru_cache
def get_settings() -> Settings:
    return Settings()
