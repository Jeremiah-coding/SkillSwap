from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    IDENTITY_SERVICE_URL: str = "http://identity-profile-service:8000"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8000"
    HTTP_TIMEOUT: float = 5.0
    INTERNAL_SERVICE_SECRET: str = "skillswap-internal-secret"


settings = Settings()
