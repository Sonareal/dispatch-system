import os
import typing

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    VERSION: str = "1.0.0"
    APP_TITLE: str = "派单管理系统"
    PROJECT_NAME: str = "派单管理系统"
    APP_DESCRIPTION: str = "多城市派单管理系统 - 工单管理、审核、指派、沟通"

    UPLOAD_DIR: str = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)), "uploads")

    CORS_ORIGINS: typing.List = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: typing.List = ["*"]
    CORS_ALLOW_HEADERS: typing.List = ["*"]

    DEBUG: bool = True

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    SECRET_KEY: str = "3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf"  # openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 day
    # Database config via environment variable
    DB_TYPE: str = os.environ.get("DB_TYPE", "sqlite")  # sqlite or postgres
    DB_HOST: str = os.environ.get("DB_HOST", "localhost")
    DB_PORT: int = int(os.environ.get("DB_PORT", "5432"))
    DB_USER: str = os.environ.get("DB_USER", "dispatch")
    DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "dispatch123")
    DB_NAME: str = os.environ.get("DB_NAME", "dispatch_db")

    @property
    def TORTOISE_ORM(self) -> dict:
        if self.DB_TYPE == "postgres":
            conn = {
                "default": {
                    "engine": "tortoise.backends.asyncpg",
                    "credentials": {
                        "host": self.DB_HOST,
                        "port": self.DB_PORT,
                        "user": self.DB_USER,
                        "password": self.DB_PASSWORD,
                        "database": self.DB_NAME,
                    },
                }
            }
        else:
            conn = {
                "default": {
                    "engine": "tortoise.backends.sqlite",
                    "credentials": {"file_path": f"{self.BASE_DIR}/db.sqlite3"},
                }
            }
        return {
            "connections": conn,
            "apps": {
                "models": {
                    "models": ["app.models", "aerich.models"],
                    "default_connection": "default",
                },
            },
            "use_tz": False,
            "timezone": "Asia/Shanghai",
        }
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # WeChat Mini Program
    WECHAT_APPID: str = os.environ.get("WECHAT_APPID", "")
    WECHAT_SECRET: str = os.environ.get("WECHAT_SECRET", "")
    WECHAT_SUBSCRIBE_TEMPLATE_ID: str = os.environ.get("WECHAT_SUBSCRIBE_TEMPLATE_ID", "")


settings = Settings()
