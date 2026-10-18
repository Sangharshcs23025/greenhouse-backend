from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "smart_greenhouse"

    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 60 * 24  # 24h, good for a mobile app

    # Shared secret the ESP32 firmware uses instead of a user JWT,
    # so the device doesn't need to "log in" like a human.
    device_api_key: str = "CHANGE_ME_DEVICE_KEY"

    class Config:
        env_file = ".env"


settings = Settings()