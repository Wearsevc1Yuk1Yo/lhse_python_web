import os
# from typing import Optional

class Settings:
    PROJECT_NAME: str = "Blog API"
    PROJECT_VERSION: str = "1.0.0"
    DATA_FILE: str = os.getenv("BLOG_DATA_FILE", "blog_data.json")

    # для базы данных
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://blog_user:blog_password@localhost/blog_db"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()
