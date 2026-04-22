import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class ConfigurationError(RuntimeError):
    pass


class Settings:
    def __init__(self) -> None:
        self.firebase_database_url = os.getenv("FIREBASE_DATABASE_URL", "")
        self.firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
        self.admin_api_token = os.getenv("ADMIN_API_TOKEN", "")
        self.app_name = os.getenv("APP_NAME", "Buoy Telemetry API")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.app_env = os.getenv("APP_ENV", "development")
        self.app_host = os.getenv("APP_HOST", "0.0.0.0")
        self.app_port = int(os.getenv("APP_PORT", "8000"))

    def validate(self) -> None:
        missing = []
        if not self.firebase_database_url:
            missing.append("FIREBASE_DATABASE_URL")
        if not self.firebase_credentials_path:
            missing.append("FIREBASE_CREDENTIALS_PATH")
        if not self.admin_api_token:
            missing.append("ADMIN_API_TOKEN")

        if missing:
            raise ConfigurationError(
                f"Missing required settings: {', '.join(missing)}"
            )

        credentials_path = Path(self.firebase_credentials_path)
        if not credentials_path.exists() or not credentials_path.is_file():
            raise ConfigurationError(
                "FIREBASE_CREDENTIALS_PATH does not point to a valid file"
            )


settings = Settings()
