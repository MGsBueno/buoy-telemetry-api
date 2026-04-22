from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.model.buoy_model import BuoyModel


class BuoyService:
    @staticmethod
    def create_buoy(buoy_id: str, name: str, token: str):
        existing = BuoyModel.get_buoy_by_id(buoy_id)
        if existing:
            raise ConflictError("Buoy already exists")

        return BuoyModel.create_buoy(buoy_id, name, token)

    @staticmethod
    def get_all_buoys():
        return BuoyModel.get_all_buoys()

    @staticmethod
    def get_buoy_by_id(buoy_id: str):
        buoy = BuoyModel.get_buoy_by_id(buoy_id)
        if not buoy:
            raise NotFoundError("Buoy not found")
        return buoy

    @staticmethod
    def update_buoy(buoy_id: str, updates: dict):
        cleaned_updates = {k: v for k, v in updates.items() if v is not None}
        buoy = BuoyModel.update_buoy(buoy_id, cleaned_updates)

        if not buoy:
            raise NotFoundError("Buoy not found")

        return buoy

    @staticmethod
    def delete_buoy(buoy_id: str):
        deleted = BuoyModel.delete_buoy(buoy_id)
        if not deleted:
            raise NotFoundError("Buoy not found")

    @staticmethod
    def create_reading(buoy_id: str, reading_data: dict):
        reading = BuoyModel.create_reading(buoy_id, reading_data)
        if not reading:
            raise NotFoundError("Buoy not found")
        return reading

    @staticmethod
    def get_all_readings(buoy_id: str):
        buoy = BuoyModel.get_buoy_by_id(buoy_id)
        if not buoy:
            raise NotFoundError("Buoy not found")
        return BuoyModel.get_all_readings(buoy_id)

    @staticmethod
    def get_reading_by_id(buoy_id: str, reading_id: str):
        reading = BuoyModel.get_reading_by_id(buoy_id, reading_id)
        if not reading:
            raise NotFoundError("Reading not found")
        return reading

    @staticmethod
    def delete_reading(buoy_id: str, reading_id: str):
        deleted = BuoyModel.delete_reading(buoy_id, reading_id)
        if not deleted:
            raise NotFoundError("Reading not found")

    @staticmethod
    def receive_telemetry(data: dict):
        if not BuoyModel.validate_buoy_token(data["device_id"], data["token"]):
            raise UnauthorizedError("Invalid buoy token")

        saved = BuoyModel.save_telemetry(data)
        if not saved:
            raise NotFoundError("Buoy not found")

        return saved
