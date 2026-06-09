from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str
    webhook_secret: str
    app_host: str
    app_port: int
    emqx_api_url: str
    emqx_api_key: str
    emqx_api_secret: str
    mqtt_topic_base: str

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
            emqx_api_url=os.getenv("EMQX_API_URL", "http://127.0.0.1:18083/api/v5"),
            emqx_api_key=os.getenv("EMQX_API_KEY", ""),
            emqx_api_secret=os.getenv("EMQX_API_SECRET", ""),
            mqtt_topic_base=os.getenv("MQTT_TOPIC_BASE", "vitam/devices"),
        )
