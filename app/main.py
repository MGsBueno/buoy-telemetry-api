import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import ConfigurationError, settings
from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.firebase import InfrastructureError
from app.routes.buoy_routes import router as buoy_router

logger = logging.getLogger("buoy_api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate()
    yield

# =========================
# APP INIT
# =========================
app = FastAPI(
    title=settings.app_name,
    description="Backend for buoy telemetry (FastAPI + Firebase)",
    version=settings.app_version,
    lifespan=lifespan,
)

# =========================
# ROUTES
# =========================
app.include_router(buoy_router)


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(_: Request, exc: ConfigurationError):
    logger.exception("Configuration error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


@app.exception_handler(InfrastructureError)
async def infrastructure_error_handler(_: Request, exc: InfrastructureError):
    logger.exception("Infrastructure error: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )


@app.exception_handler(ConflictError)
async def conflict_error_handler(_: Request, exc: ConflictError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(NotFoundError)
async def not_found_error_handler(_: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


@app.exception_handler(UnauthorizedError)
async def unauthorized_error_handler(_: Request, exc: UnauthorizedError):
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
    )

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {
        "message": f"{settings.app_name} is running",
        "docs": "/docs"
    }

# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
def health():
    return {
        "status": "ok",
        "environment": settings.app_env,
    }
