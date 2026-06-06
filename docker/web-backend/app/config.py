from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str
    webhook_secret: str
    app_host: str
    app_port: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.getenv(
                "DATABASE_URL",
                "mysql+pymysql://iot:iot_dev_password@127.0.0.1:3306/iot_server",
            ),
            webhook_secret=os.getenv("EMQX_WEBHOOK_SECRET", ""),
            app_host=os.getenv("APP_HOST", "127.0.0.1"),
            app_port=int(os.getenv("APP_PORT", "8000")),
        )
