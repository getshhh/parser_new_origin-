import os
from pathlib import Path
from typing import Optional

from pydantic import PostgresDsn, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class PathConfig(BaseModel):
    # Строка, чтобы os.path.join работал без приведения типов
    root: str = str(Path(__file__).parent.parent.parent)
    log_dir: str = os.path.join(root, "logs")

    info_log_file: str = os.path.join(log_dir, "info.log")
    error_log_file: str = os.path.join(log_dir, "error.log")


class DatabaseConfig(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10


class BotConfig(BaseModel):
    token: str
    admin_ids: str

    @property
    def get_admins(self) -> list[int]:
        return list(map(int, self.admin_ids.split(",")))


class BrowserConfig(BaseModel):
    # Делаем опциональным — чтобы BrowserConfig() не требовал обязательных переменных
    token: Optional[str] = None
    # Включает видимый режим браузера при отладке (False = headless)
    debug_mode: bool = False
    # Если None — определим автоматически: на Windows False, иначе True
    use_virtual_display: Optional[bool] = None

    # Текст для вашего пайплайна/оценки — оставлен как был
    base_content: str = """Твоя задача:
1. Отфильтровать только те сообщения, у которых тема — "вакансия".
2. Оценить каждое сообщение по качеству и соответствию теме. 
   - Самые лучшие сообщения: чётко сформулированы, содержат ключевые детали (зарплата, обязанности, требования и контакты).
   - Хорошие сообщения: качественные, но менее подробные или содержат незначительные излишества.
3. Выбрать максимум 2 записи из списка (1 или 2, но не больше), которые лучше всего соответствуют этим критериям.

Вернуть результат в формате JSON. Каждый объект должен содержать:
- "id" сообщения.
- Поле "good", принимающее значение:
  - True для самых лучших сообщений.
  - False для сообщений второй категории.

Если тема сообщения не "вакансия", пропустить его."""


class VKConfig(BaseModel):
    token: str
    url_get: str


class UserBotConfig(BaseModel):
    api_id: int
    api_hash: str
    phone: str
    name: str


# Минимальная модель AI-конфига, чтобы не падало без переменных окружения
class OpenAIConfig(BaseModel):
    # Поддерживаем оба варианта имён, чтобы не ловить AttributeError
    token: Optional[str] = None          # из ENV: ROOT__AI__TOKEN
    api_key: Optional[str] = None        # из ENV: ROOT__AI__API_KEY
    base_url: Optional[str] = None       # из ENV: ROOT__AI__BASE_URL (если нужен кастом)
    model: str = "gpt-4o-mini"


class Settings(BaseSettings):
    # Базовые блоки
    path: PathConfig = PathConfig()
    db: DatabaseConfig
    bot: BotConfig
    userbot: UserBotConfig
    vk: VKConfig
    ai: OpenAIConfig = OpenAIConfig()
    

    # Поля, которые используют ваши парсеры
    browser: BrowserConfig = BrowserConfig()
    parser_interval_sec: int = 60

    # Общие переменные окружения
    proxy: str
    gmail_user: str
    gmail_password: str

    # Конфиг pydantic-settings
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="ROOT__",
        extra="ignore",  # <- игнорируем лишние ключи из .env (например ROOT__CHANNEL__KWORK)
    )


class KworkSettings(BaseSettings):
    channel_id: int = -1002022051080  # Дефолтный канал
    check_interval: int = 1800  # 30 минут


settings = Settings()
