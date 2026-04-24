# Buoy Telemetry API

A lightweight telemetry ingestion API for connected buoys, built with FastAPI and Firebase Realtime Database.

Current release status: `v0.1.0-alpha.1`

The platform is organized around two primary flows:

- devices send telemetry to `/telemetry` using the buoy token;
- operators manage buoys and readings through endpoints protected by `X-Admin-Token`.

## Documentation

- [Architecture](docs/architecture.md): system structure, Google Cloud ecosystem, and design decisions
- [Setup and Deployment](docs/setup-and-deployment.md): local setup, configuration, testing, and Cloud Run deployment

## Product Scope

- onboard and manage buoy devices;
- ingest telemetry from field devices;
- store cumulative readings in Firebase Realtime Database;
- expose admin endpoints for operational control and retrieval;
- provide interactive API documentation at `/docs`.

## Quick Start

Use `.env.example` as the starting point, then run:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Useful URLs:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`

For detailed setup, configuration, testing, and deployment guidance, see [docs/setup-and-deployment.md](docs/setup-and-deployment.md).

## Authentication

### Telemetry

`POST /telemetry`

The device sends:

- `device_id`
- `device_name`
- `token`
- reading data

The `token` field must contain the registered buoy token.

### Admin Endpoints

All `/buoys` endpoints require this header:

```text
X-Admin-Token: your-admin-token
```

These endpoints do not return the buoy token in their responses.

## Example Requests

### Create a Buoy

```bash
curl -X POST "http://127.0.0.1:8000/buoys/b1" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: your-admin-token" \
  -d '{
    "name": "Alpha Buoy",
    "token": "buoy-secret-token"
  }'
```

### Send Telemetry

```bash
curl -X POST "http://127.0.0.1:8000/telemetry" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "b1",
    "device_name": "Alpha Buoy",
    "token": "buoy-secret-token",
    "temperature": 24.5,
    "battery_voltage": 12.38,
    "latitude": -23.5505,
    "longitude": -46.6333
  }'
```

Expected response:

```json
{
  "id": "reading-1",
  "temperature": 24.5,
  "battery_voltage": 12.38,
  "latitude": -23.5505,
  "longitude": -46.6333,
  "timestamp": 1710000000
}
```

### List Buoys

```bash
curl -X GET "http://127.0.0.1:8000/buoys" \
  -H "X-Admin-Token: your-admin-token"
```

## Why Not Use Firebase Directly on the Device?

This API intentionally sits between the device and Firebase.

That architectural decision keeps the system safer and easier to operate:

- the Firebase service account stays on the backend, never on the device;
- business rules stay centralized in one place;
- device tokens can be validated before data reaches the database;
- the backend can evolve without reflashing device logic for every backend change;
- monitoring, rate limiting, and auditing are easier to add at the API layer.

## Future Improvements

- device retry and local buffering for intermittent connectivity;
- anomaly detection for battery and temperature data;
- time-series aggregation endpoints for reporting;
- Grafana or dashboard integration for operations and monitoring.
