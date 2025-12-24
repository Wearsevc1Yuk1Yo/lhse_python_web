import os

from dotenv import load_dotenv

# from typing import Optional


load_dotenv(encoding="utf-8")


class Settings:
    PROJECT_NAME: str = "Blog API"
    PROJECT_VERSION: str = "1.0.0"
    DATA_FILE: str = os.getenv("BLOG_DATA_FILE", "blog_data.json")

    # для базы данных
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://blog_user:blog_password@localhost:5432/blog_db"
    )

    # not sure bout this thing tho
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "D4J8tQZkXe2YpL6mH7nB9vC0xS1wF3gR5hN2jK8lP0oI7uY"
    )

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()
