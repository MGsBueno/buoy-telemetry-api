from tests.conftest import admin_headers


def test_full_buoy_crud_and_telemetry_flow(functional_client):
    response = functional_client.get("/buoys", headers=admin_headers())
    assert response.status_code == 200
    assert response.json() == []

    response = functional_client.post(
        "/buoys/b1",
        json={"name": "Alpha", "token": "abc$123"},
        headers=admin_headers(),
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": "b1",
        "name": "Alpha",
    }

    response = functional_client.get("/buoys/b1", headers=admin_headers())
    assert response.status_code == 200
    assert response.json() == {
        "id": "b1",
        "name": "Alpha",
    }

    response = functional_client.put(
        "/buoys/b1",
        json={"name": "Alpha 2", "token": "abc$123"},
        headers=admin_headers(),
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": "b1",
        "name": "Alpha 2",
    }

    response = functional_client.post(
        "/buoys/b1/readings",
        json={
            "temperature": 24.5,
            "battery_voltage": 3.7,
            "latitude": -23.55,
            "longitude": -46.63,
        },
        headers=admin_headers(),
    )
    assert response.status_code == 200
    created_reading = response.json()
    assert created_reading == {
        "id": "reading-1",
        "temperature": 24.5,
        "battery_voltage": 3.7,
        "latitude": -23.55,
        "longitude": -46.63,
        "timestamp": 1710000000,
    }

    response = functional_client.get("/buoys/b1/readings", headers=admin_headers())
    assert response.status_code == 200
    assert response.json() == [created_reading]

    response = functional_client.get("/buoys/b1/readings/reading-1", headers=admin_headers())
    assert response.status_code == 200
    assert response.json() == created_reading

    response = functional_client.post(
        "/telemetry",
        json={
            "device_id": "b1",
            "device_name": "Telemetry Name",
            "token": "abc$123",
            "temperature": 25.1,
            "battery_voltage": 3.8,
            "latitude": -23.56,
            "longitude": -46.64,
        },
    )
    assert response.status_code == 200
    telemetry_reading = response.json()
    assert telemetry_reading == {
        "id": "reading-2",
        "temperature": 25.1,
        "battery_voltage": 3.8,
        "latitude": -23.56,
        "longitude": -46.64,
        "timestamp": 1710000000,
    }

    response = functional_client.get("/buoys/b1", headers=admin_headers())
    assert response.status_code == 200
    assert response.json() == {
        "id": "b1",
        "name": "Telemetry Name",
    }

    response = functional_client.get("/buoys/b1/readings", headers=admin_headers())
    assert response.status_code == 200
    assert response.json() == [created_reading, telemetry_reading]

    response = functional_client.delete("/buoys/b1/readings/reading-1", headers=admin_headers())
    assert response.status_code == 200
    assert response.json() == {"message": "Reading deleted successfully"}

    response = functional_client.get("/buoys/b1/readings", headers=admin_headers())
    assert response.status_code == 200
    assert response.json() == [telemetry_reading]

    response = functional_client.delete("/buoys/b1", headers=admin_headers())
    assert response.status_code == 200
    assert response.json() == {"message": "Buoy deleted successfully"}

    response = functional_client.get("/buoys/b1", headers=admin_headers())
    assert response.status_code == 404
    assert response.json() == {"detail": "Buoy not found"}


def test_telemetry_rejects_invalid_token(functional_client):
    functional_client.post(
        "/buoys/b1",
        json={"name": "Alpha", "token": "abc$123"},
        headers=admin_headers(),
    )

    response = functional_client.post(
        "/telemetry",
        json={
            "device_id": "b1",
            "device_name": "Alpha",
            "token": "wrong-token",
            "temperature": 24.5,
            "battery_voltage": 3.7,
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid buoy token"}
