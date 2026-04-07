"""
Core application settings.

All configuration values are read from environment variables.
Defaults are provided for local development only.
"""
import os


class Settings:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-me-in-production-32-chars!!")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./todo.db")
    CORS_ORIGIN: str = os.environ.get("CORS_ORIGIN", "https://sdd-todo-challange.vercel.app")


settings = Settings()
