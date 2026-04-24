# Setup and Deployment

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
- on Cloud Run, inject the Firebase credential file from Secret Manager and point `FIREBASE_CREDENTIALS_PATH` to that mounted file;
- replace all example values before deploying.

## Running Locally

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Useful URLs:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`

## Tests

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q tests
```

The test suite includes:

- API tests with mocks;
- functional tests with an in-memory Firebase-like layer.

## Cloud Run Deployment

This project is ready to be containerized and deployed to Google Cloud Run.

### Recommended approach

- use Cloud Run with a dedicated runtime service account;
- grant that service account access to Firebase Realtime Database;
- do not bake or deploy `serviceAccountKey.json` into the container image;
- store the Firebase JSON in Secret Manager and mount it into Cloud Run as a file;
- set `FIREBASE_CREDENTIALS_PATH` to the mounted secret file path;
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
  --set-env-vars FIREBASE_DATABASE_URL=https://YOUR_PROJECT_ID-default-rtdb.firebaseio.com,FIREBASE_CREDENTIALS_PATH=/secrets/firebase/service-account.json,ADMIN_API_TOKEN=your-admin-token,APP_ENV=production \
  --update-secrets /secrets/firebase/service-account.json=FIREBASE_SERVICE_ACCOUNT_SECRET:latest
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
  --substitutions=_SERVICE_NAME=buoy-telemetry-api,_REGION=us-central1,_APP_ENV=production,_FIREBASE_DATABASE_URL=https://YOUR_PROJECT_ID-default-rtdb.firebaseio.com,_ADMIN_API_TOKEN=your-admin-token,_RUNTIME_SERVICE_ACCOUNT=your-cloud-run-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com,_FIREBASE_SECRET_NAME=firebase-service-account,_FIREBASE_SECRET_MOUNT_PATH=/secrets/firebase/service-account.json
```

### Secret Manager setup

Create or update the Firebase credential secret and grant access to the Cloud Run runtime service account:

```powershell
.\scripts\setup-cloud-run-secret.ps1 `
  -ProjectId YOUR_PROJECT_ID `
  -RuntimeServiceAccount your-cloud-run-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com `
  -SecretName firebase-service-account `
  -CredentialFile .\serviceAccountKey.json
```

This script:

- creates the secret if it does not exist;
- uploads the current JSON as a new secret version;
- grants `roles/secretmanager.secretAccessor` to the runtime service account.

### GitHub Actions deployment

This repository also includes `.github/workflows/deploy-cloud-run.yml`.

Recommended authentication is Workload Identity Federation.

Required GitHub repository secrets:

- `GCP_PROJECT_ID`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_DEPLOY_SERVICE_ACCOUNT`
- `GCP_RUNTIME_SERVICE_ACCOUNT`
- `FIREBASE_DATABASE_URL`
- `ADMIN_API_TOKEN`
- `FIREBASE_SERVICE_ACCOUNT_SECRET`

The workflow:

- authenticates to Google Cloud;
- builds and pushes the container image;
- deploys the current revision to Cloud Run;
- mounts the Firebase JSON secret at `/secrets/firebase/service-account.json`;
- sets `FIREBASE_CREDENTIALS_PATH` to that mounted file.
