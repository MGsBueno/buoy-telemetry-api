from app.schemas.buoy_schema import BuoyCreate, BuoyUpdate, ReadingCreate, TelemetryIn
from app.services.buoy_service import BuoyService


class BuoyController:
    @staticmethod
    def create_buoy(buoy_id: str, payload: BuoyCreate):
        return BuoyService.create_buoy(
            buoy_id=buoy_id,
            name=payload.name,
            token=payload.token
        )

    @staticmethod
    def list_buoys():
        return BuoyService.get_all_buoys()

    @staticmethod
    def get_buoy(buoy_id: str):
        return BuoyService.get_buoy_by_id(buoy_id)

    @staticmethod
    def update_buoy(buoy_id: str, payload: BuoyUpdate):
        return BuoyService.update_buoy(buoy_id, payload.model_dump())

    @staticmethod
    def delete_buoy(buoy_id: str):
        BuoyService.delete_buoy(buoy_id)
        return {"message": "Buoy deleted successfully"}

    @staticmethod
    def create_reading(buoy_id: str, payload: ReadingCreate):
        return BuoyService.create_reading(buoy_id, payload.model_dump())

    @staticmethod
    def list_readings(buoy_id: str):
        return BuoyService.get_all_readings(buoy_id)

    @staticmethod
    def get_reading(buoy_id: str, reading_id: str):
        return BuoyService.get_reading_by_id(buoy_id, reading_id)

    @staticmethod
    def delete_reading(buoy_id: str, reading_id: str):
        BuoyService.delete_reading(buoy_id, reading_id)
        return {"message": "Reading deleted successfully"}

    @staticmethod
    def receive_telemetry(payload: TelemetryIn):
        return BuoyService.receive_telemetry(payload.model_dump())
