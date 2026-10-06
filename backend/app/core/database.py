import os
from typing import Generator
from dotenv import load_dotenv
from sqlmodel import Session, create_engine

# Load environment variables from backend/.env or parent .env
load_dotenv()

# Read DATABASE_URL from environment variable without hardcoding credentials
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///database.db"
)

# Create SQLModel / SQLAlchemy engine
# pool_pre_ping ensures stale connections are recycled
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True
)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency to provide a transactional database session."""
    with Session(engine) as session:
        yield session
