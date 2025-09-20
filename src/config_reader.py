import os
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    PARSING_INTERVAL: int = 300  # 5 минут
    MAX_PAGES: int = 5
    ROOT__VK__TOKEN: str | None = None
    ROOT__VK__URL_GET: str | None = "https://api.vk.com/method/wall.get"
    PARSING_INTERVAL: int = 300
    ROOT__VK__GROUPS: str | None = "-1"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8"
    )

config = Settings()