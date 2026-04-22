# Buoy Telemetry API

A lightweight API for buoy telemetry ingestion built with FastAPI and Firebase Realtime Database.

Current release status: `v0.1.0-alpha.1`

It is organized around two main flows:

- devices send telemetry to `/telemetry` using the buoy token;
- operators manage buoys and readings through endpoints protected by `X-Admin-Token`.

## What the API Does

- creates, lists, updates, and deletes buoys;
- stores manual readings and telemetry readings;
- persists data in Firebase Realtime Database;
- exposes interactive documentation at `/docs`.

## Requirements

- Python 3.12+
- a Firebase service account credential
- Firebase Realtime Database enabled in your project

## Configuration

Use `.env.example` as the starting point.

Main variables:

- `FIREBASE_DATABASE_URL`: Realtime Database URL
- `FIREBASE_CREDENTIALS_PATH`: path to the Firebase service account JSON for local development
- `ADMIN_API_TOKEN`: token required for admin endpoints
- `APP_ENV`: `development`, `staging`, or `production`

Notes:

- do not expose `serviceAccountKey.json`;
- do not reuse the admin token on devices;
- on Cloud Run, prefer the runtime service account instead of mounting a local JSON key;
- replace all example values before deploying.

## Running Locally

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Useful URLs:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`

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

That design helps keep the system safer and easier to operate:

- the Firebase service account stays on the backend, never on the device;
- business rules stay centralized in one place;
- device tokens can be validated before data reaches the database;
- the backend can evolve without reflashing device logic for every backend change;
- monitoring, rate limiting, and auditing are easier to add at the API layer.

## Tests

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q tests
```

The test suite includes:

- API tests with mocks;
- functional tests with an in-memory Firebase-Like layer.

## Cloud Run Deployment

This project is ready to be containerized and deployed to Google Cloud Run.

### Recommended approach

- use Cloud Run with a dedicated runtime service account;
- grant that service account access to Firebase Realtime Database;
- do not deploy `serviceAccountKey.json` to production;
- set `FIREBASE_DATABASE_URL`, `ADMIN_API_TOKEN`, and `APP_ENV` as environment variables.

### Build and deploy

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/buoy-telemetry-api
```

```bash
gcloud run deploy buoy-telemetry-api \
  --image gcr.io/PROJECT_ID/buoy-telemetry-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account YOUR_CLOUD_RUN_SERVICE_ACCOUNT \
  --set-env-vars FIREBASE_DATABASE_URL=https://YOUR_PROJECT_ID-default-rtdb.firebaseio.com,ADMIN_API_TOKEN=your-admin-token,APP_ENV=production
```

### Local container test

```bash
docker build -t buoy-telemetry-api .
docker run --rm -p 8080:8080 \
  -e FIREBASE_DATABASE_URL=https://YOUR_PROJECT_ID-default-rtdb.firebaseio.com \
  -e FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json \
  -e ADMIN_API_TOKEN=your-admin-token \
  -e APP_ENV=development \
  buoy-telemetry-api
```

### Cloud Build

This repository includes a `cloudbuild.yaml` that:
- builds the container image;
- tags it with `latest` and the commit SHA;
- deploys the service to Cloud Run.

Before using it, update the substitutions in `cloudbuild.yaml` or override them at submit time.

Example:

```bash
gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions=_SERVICE_NAME=buoy-telemetry-api,_REGION=us-central1,_APP_ENV=production,_FIREBASE_DATABASE_URL=https://YOUR_PROJECT_ID-default-rtdb.firebaseio.com,_ADMIN_API_TOKEN=your-admin-token,_RUNTIME_SERVICE_ACCOUNT=your-cloud-run-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### GitHub Actions Deployment

This repository also includes `.github/workflows/deploy-cloud-run.yml`.

Recommended authentication is Workload Identity Federation.

Required GitHub repository secrets:
- `GCP_PROJECT_ID`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_DEPLOY_SERVICE_ACCOUNT`
- `GCP_RUNTIME_SERVICE_ACCOUNT`
- `FIREBASE_DATABASE_URL`
- `ADMIN_API_TOKEN`

The workflow:
- authenticates to Google Cloud;
- builds and pushes the container image;
- deploys the current revision to Cloud Run.

## Future Improvements

- device retry and local buffering for intermittent connectivity;
- anomaly detection for battery and temperature data;
- time-series aggregation endpoints for reporting;
- Grafana or dashboard integration for operations and monitoring.
