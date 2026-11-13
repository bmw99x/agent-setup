from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHOP_")

    database_url: str = "postgresql+asyncpg://shop:shop@localhost:5432/shop"
    smtp_host: str = "localhost"
    smtp_from: str = "orders@shop.example"
    sms_gateway_url: str = "https://sms.example.invalid/v1"
    sms_gateway_api_key: str = ""
    push_gateway_url: str = "https://push.example.invalid/v2"
    push_gateway_api_key: str = ""


settings = Settings()
