# Architectural Report

## Overview

The current ecosystem was designed to solve an IoT telemetry problem in a simple, operational, and extensible way: A buoy measures data such as temperature in the field, sends readings to a public API, and that API validates device identity, persists the data, and exposes administrative endpoints for management and retrieval.

The architecture clearly separates device, backend, and storage responsibilities:

- At the edge, an Arduino with a DS18B20 sensor and a SIM800L module performs measurement and transmission.
- In the backend, a FastAPI application acts as the control, authentication, and business-rule layer.
- In storage, Firebase Realtime Database serves as the operational data store for simple entities and cumulative time-series readings.

## Backend Architecture

The backend follows a layered organization with explicit responsibility boundaries:

- `Routes` handle HTTP exposure through FastAPI.
- `Schemas` define request and response contracts using Pydantic.
- `Controller` acts as the entry orchestration layer.
- `Service` contains business rules and validation logic.
- `Model` handles persistence and Firebase interaction.

In practice, this results in a structure close to a classic layered architecture:

`Router -> Controller -> Service -> Model/Infrastructure`

This decision keeps the code readable, testable, and easier to evolve without coupling business rules directly to Firebase.

A clear example is the `/telemetry` flow. The API does not blindly persist incoming data. Instead, it:

1. validates the buoy token,
2. verifies that the buoy exists,
3. updates buoy metadata if needed,
4. appends a new reading with a server-generated timestamp.

This reinforces the principle that devices do not talk directly to the database and that data governance remains centralized in the backend.

## Domain Model

The current functional model revolves around two main entities:

### Buoy

- `id`
- `name`
- `token`

### Reading

- `temperature`
- `battery_voltage`
- `latitude`
- `longitude`
- `timestamp`

Readings are stored using an append-only strategy through Firebase `push`, which is well suited for lightweight time-series telemetry. Each new measurement becomes a new record rather than overwriting previous state.

This design supports:

- cumulative historical records,
- auditability,
- future CSV export,
- simple analytics over time.

Generating the `timestamp` in the backend instead of on the Arduino is also an important architectural choice. It avoids reliance on device-local clocks, centralizes the time reference, and keeps stored records consistent.

## Device Architecture

On the edge side, the Arduino firmware was aligned with the actual API contract. The telemetry payload matches the backend schema exactly:

- `device_id`
- `device_name`
- `token`
- `temperature`
- `battery_voltage`
- `latitude`
- `longitude`

Another relevant design choice was replacing the original weak static token with a stronger static token. While this is not a full security solution for embedded environments, it is an appropriate improvement for the current stage without introducing unnecessary operational complexity.

## Data Flow

The current data flow is straightforward:

1. The buoy reads the temperature from the DS18B20 sensor.
2. The Arduino assembles a telemetry payload.
3. The SIM800L sends the payload to the backend API.
4. The backend validates the buoy identity using the stored token.
5. The backend appends a new reading to Firebase Realtime Database.
6. Administrative clients can retrieve buoy metadata and the full reading history through protected endpoints.

This flow intentionally places the API between the device and Firebase.

## Google Cloud Ecosystem

The solution is deployed on a Google Cloud stack chosen for low operational overhead and low cost:

- **Cloud Run** hosts the FastAPI service in a serverless model.
- **Artifact Registry** stores container images.
- **Secret Manager** stores the Firebase credential file and injects it into the runtime as a mounted secret.
- **Firebase Realtime Database** stores buoys and readings.
- **GitHub Actions + Workload Identity Federation** provide CI/CD without static cloud deployment keys.

This ecosystem fits the current system profile well: low request volume, bursty telemetry, and a need for quick deployment without infrastructure administration.

## CI/CD and Delivery Model

The deployment pipeline uses GitHub Actions to:

1. authenticate to Google Cloud through Workload Identity Federation,
2. build the container image,
3. push the image to the registry,
4. deploy the new revision to Cloud Run.

This approach avoids long-lived JSON keys for deployment and keeps the delivery flow aligned with modern cloud security practices.

A key operational improvement was mounting the Firebase credential file from Secret Manager into the Cloud Run runtime instead of baking it into the image. This separates build artifacts from secrets, improves security posture, and simplifies future rotation of sensitive credentials.

## Architectural Decisions

Several decisions shaped the current system:

### 1. Devices do not access Firebase directly

This was an important decision because it:

- prevents embedding Firebase administrative credentials in the device,
- centralizes buoy authentication in the backend,
- creates a single place for future rules such as rate limiting, auditing, token rotation, and payload normalization.

### 2. Cloud Run instead of fixed infrastructure

Cloud Run was chosen because:

- telemetry traffic is light and intermittent,
- serverless reduces operational burden,
- cost remains very low at the current scale.

### 3. Secret Manager instead of embedding credentials in the image

This separates deployment artifacts from secrets and avoids shipping sensitive material inside the container.

### 4. Simple domain model with cumulative append-only readings

This matches the current requirements well and keeps the system easy to reason about and operate.

## Trade-offs

The current design makes conscious trade-offs.

### Static per-buoy token

This is simple and functional for the current phase, but it is still a moderate security model for real IoT deployments. A stronger future approach would be:

- HMAC-signed payloads,
- signed timestamps,
- per-device provisioning,
- stronger replay protection.

### Firebase Realtime Database

This is a good operational fit today, but if the system grows significantly, an aggregation layer or more analytical storage strategy may become necessary.

### Runtime identity

Using the default compute service account helped unblock the deployment quickly, but the preferred long-term state is a dedicated Cloud Run runtime service account with minimum required privileges.

### Registry path

The current deployment path using `gcr.io` works, but the natural evolution is moving explicitly to a `*.pkg.dev` Artifact Registry path.

## Current State

The current architecture is:

- small,
- coherent,
- functional,
- low-cost,
- easy to evolve.

The backend is well organized in layers, the device sends a payload aligned with the API contract, and the Google Cloud deployment now follows a practical and reasonably secure serverless model.

The ecosystem already supports:

- telemetry ingestion,
- buoy-level authentication,
- cumulative reading history,
- admin management endpoints,
- CSV export from collected readings,
- automated deployment through GitHub Actions.

## Possible Next Improvements

- Replace the current runtime identity with a dedicated Cloud Run service account.
- Move image publishing to an explicit Artifact Registry repository path under `*.pkg.dev`.
- Consolidate deployment and operating procedures into repository documentation.
- Add a post-deploy smoke test for `/health` and `/docs`.
- Consider evolving buoy authentication from static tokens to HMAC-based request validation.
- Introduce optional reporting or aggregation endpoints if historical usage increases.

## Conclusion

The current system provides a solid foundation for an IoT telemetry workflow with a clear separation between edge, API, and storage concerns. The implementation choices prioritize delivery speed, operational simplicity, and low cost, while still leaving room for future hardening in security, runtime identity, and storage strategy.

At its current stage, the architecture is appropriate, internally consistent, and well positioned for controlled evolution.
