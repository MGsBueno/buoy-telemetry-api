import time
from typing import Optional
from app.core.firebase import get_database_reference


class BuoyModel:
    BASE_PATH = "buoys"

    @staticmethod
    def _serialize_buoy(buoy_id: str, buoy_data: dict) -> dict:
        return {
            "id": buoy_id,
            "name": buoy_data.get("name"),
        }

    @classmethod
    def create_buoy(cls, buoy_id: str, name: str, token: str) -> dict:
        ref = get_database_reference(f"{cls.BASE_PATH}/{buoy_id}")
        payload = {
            "name": name,
            "token": token,
            "readings": {}
        }
        ref.set(payload)
        return cls._serialize_buoy(buoy_id, payload)

    @classmethod
    def get_all_buoys(cls) -> list[dict]:
        ref = get_database_reference(cls.BASE_PATH)
        data = ref.get() or {}

        result = []
        for buoy_id, buoy_data in data.items():
            result.append(cls._serialize_buoy(buoy_id, buoy_data))
        return result

    @classmethod
    def get_buoy_by_id(cls, buoy_id: str) -> Optional[dict]:
        ref = get_database_reference(f"{cls.BASE_PATH}/{buoy_id}")
        data = ref.get()

        if not data:
            return None

        return cls._serialize_buoy(buoy_id, data)

    @classmethod
    def update_buoy(cls, buoy_id: str, updates: dict) -> Optional[dict]:
        ref = get_database_reference(f"{cls.BASE_PATH}/{buoy_id}")
        current = ref.get()

        if not current:
            return None

        ref.update(updates)
        updated = ref.get()

        return cls._serialize_buoy(buoy_id, updated)

    @classmethod
    def delete_buoy(cls, buoy_id: str) -> bool:
        ref = get_database_reference(f"{cls.BASE_PATH}/{buoy_id}")
        current = ref.get()

        if not current:
            return False

        ref.delete()
        return True

    @classmethod
    def create_reading(cls, buoy_id: str, reading_data: dict) -> Optional[dict]:
        buoy_ref = get_database_reference(f"{cls.BASE_PATH}/{buoy_id}")
        buoy = buoy_ref.get()

        if not buoy:
            return None

        readings_ref = get_database_reference(f"{cls.BASE_PATH}/{buoy_id}/readings")
        payload = {
            "temperature": reading_data["temperature"],
            "battery_voltage": reading_data["battery_voltage"],
            "latitude": reading_data.get("latitude"),
            "longitude": reading_data.get("longitude"),
            "timestamp": int(time.time())
        }

        new_ref = readings_ref.push(payload)

        return {
            "id": new_ref.key,
            **payload
        }

    @classmethod
    def get_all_readings(cls, buoy_id: str) -> list[dict]:
        ref = get_database_reference(f"{cls.BASE_PATH}/{buoy_id}/readings")
        data = ref.get() or {}

        result = []
        for reading_id, reading_data in data.items():
            result.append({
                "id": reading_id,
                **reading_data
            })

        return result

    @classmethod
    def get_reading_by_id(cls, buoy_id: str, reading_id: str) -> Optional[dict]:
        ref = get_database_reference(f"{cls.BASE_PATH}/{buoy_id}/readings/{reading_id}")
        data = ref.get()

        if not data:
            return None

        return {
            "id": reading_id,
            **data
        }

    @classmethod
    def delete_reading(cls, buoy_id: str, reading_id: str) -> bool:
        ref = get_database_reference(f"{cls.BASE_PATH}/{buoy_id}/readings/{reading_id}")
        current = ref.get()

        if not current:
            return False

        ref.delete()
        return True

    @classmethod
    def validate_buoy_token(cls, buoy_id: str, token: str) -> bool:
        ref = get_database_reference(f"{cls.BASE_PATH}/{buoy_id}")
        data = ref.get()

        if not data:
            return False

        return data.get("token") == token

    @classmethod
    def save_telemetry(cls, telemetry_data: dict) -> Optional[dict]:
        buoy_id = telemetry_data["device_id"]

        buoy_ref = get_database_reference(f"{cls.BASE_PATH}/{buoy_id}")
        buoy = buoy_ref.get()

        if not buoy:
            return None

        buoy_ref.update({"name": telemetry_data["device_name"]})

        readings_ref = get_database_reference(f"{cls.BASE_PATH}/{buoy_id}/readings")
        payload = {
            "temperature": telemetry_data["temperature"],
            "battery_voltage": telemetry_data["battery_voltage"],
            "latitude": telemetry_data.get("latitude"),
            "longitude": telemetry_data.get("longitude"),
            "timestamp": int(time.time())
        }

        new_ref = readings_ref.push(payload)

        return {
            "id": new_ref.key,
            **payload
        }
