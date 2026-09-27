import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Application configuration
    APP_NAME: str = "AI-Powered CRM Lead Prioritization"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Database connection configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/crm_db")
    SQL_ECHO: bool = os.getenv("SQL_ECHO", "false").lower() == "true"

    # Model artifact configuration
    MODEL_PATH: str = os.getenv("MODEL_PATH", "data/model.joblib")

    # Optional: LLM configuration
    LLM_API_KEY: str | None = os.getenv("LLM_API_KEY")

settings = Settings()

