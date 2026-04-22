from threading import Lock

import firebase_admin
from firebase_admin import credentials, db
from app.core.config import ConfigurationError, settings


class InfrastructureError(RuntimeError):
    pass


_firebase_lock = Lock()


def get_firebase_app():
    settings.validate()

    try:
        with _firebase_lock:
            if not firebase_admin._apps:
                cred = credentials.Certificate(settings.firebase_credentials_path)
                firebase_admin.initialize_app(
                    cred,
                    {"databaseURL": settings.firebase_database_url}
                )
            return firebase_admin.get_app()
    except ConfigurationError:
        raise
    except Exception as exc:
        raise InfrastructureError("Failed to initialize Firebase") from exc


def get_database_reference(path: str):
    get_firebase_app()
    try:
        return db.reference(path)
    except Exception as exc:
        raise InfrastructureError("Failed to access Firebase database") from exc
