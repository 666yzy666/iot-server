from app.database import engine
from app.models import Base


def main() -> None:
    Base.metadata.create_all(engine)
    print("database tables initialized")


if __name__ == "__main__":
    main()
