from sqlalchemy import create_engine

from config.settings import Settings
from models.base import Base


def main() -> None:
    settings = Settings.from_env()
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(engine)
    print("database tables initialized")


if __name__ == "__main__":
    main()