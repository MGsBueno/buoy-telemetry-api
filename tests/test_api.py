from app.core.exceptions import ConflictError, UnauthorizedError
from app.services.buoy_service import BuoyService
from tests.conftest import admin_headers, create_client


def test_root_endpoint():
    client = create_client()

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Buoy Telemetry API is running",
        "docs": "/docs",
    }


def test_health_endpoint():
    client = create_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "environment": "development",
    }


def test_list_buoys_returns_service_data(monkeypatch):
    client = create_client()
    expected = [{"id": "b1", "name": "Alpha"}]

    monkeypatch.setattr(BuoyService, "get_all_buoys", staticmethod(lambda: expected))

    response = client.get("/buoys", headers=admin_headers())

    assert response.status_code == 200
    assert response.json() == expected


def test_create_buoy_returns_created_payload(monkeypatch):
    client = create_client()

    def fake_create_buoy(buoy_id: str, name: str, token: str):
        return {"id": buoy_id, "name": name}

    monkeypatch.setattr(BuoyService, "create_buoy", staticmethod(fake_create_buoy))

    response = client.post(
        "/buoys/b1",
        json={"name": "Alpha", "token": "abc$123"},
        headers=admin_headers(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "b1",
        "name": "Alpha",
    }


def test_create_buoy_returns_400_when_service_rejects(monkeypatch):
    client = create_client()

    def fake_create_buoy(**_kwargs):
        raise ConflictError("Buoy already exists")

    monkeypatch.setattr(BuoyService, "create_buoy", staticmethod(fake_create_buoy))

    response = client.post(
        "/buoys/b1",
        json={"name": "Alpha", "token": "abc$123"},
        headers=admin_headers(),
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Buoy already exists"}


def test_admin_routes_require_admin_token():
    client = create_client()

    response = client.get("/buoys")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid admin token"}


def test_receive_telemetry_returns_401_when_buoy_token_is_invalid(monkeypatch):
    client = create_client()

    def fake_receive_telemetry(_data: dict):
        raise UnauthorizedError("Invalid buoy token")

    monkeypatch.setattr(BuoyService, "receive_telemetry", staticmethod(fake_receive_telemetry))

    response = client.post(
        "/telemetry",
        json={
            "device_id": "b1",
            "device_name": "Alpha",
            "token": "wrong",
            "temperature": 24.5,
            "battery_voltage": 3.7,
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid buoy token"}


def test_receive_telemetry_returns_saved_payload(monkeypatch):
    client = create_client()
    saved = {
        "id": "reading-1",
        "temperature": 24.5,
        "battery_voltage": 3.7,
        "latitude": -23.55,
        "longitude": -46.63,
        "timestamp": 1710000000,
    }

    monkeypatch.setattr(BuoyService, "receive_telemetry", staticmethod(lambda _data: saved))

    response = client.post(
        "/telemetry",
        json={
            "device_id": "b1",
            "device_name": "Alpha",
            "token": "abc$123",
            "temperature": 24.5,
            "battery_voltage": 3.7,
            "latitude": -23.55,
            "longitude": -46.63,
        },
    )

    assert response.status_code == 200
    assert response.json() == saved
