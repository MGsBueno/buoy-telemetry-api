from fastapi import APIRouter, Depends

from app.core.auth import verify_admin_token
from app.controllers.buoy_controller import BuoyController
from app.schemas.buoy_schema import (
    BuoyCreate,
    BuoyResponse,
    BuoyUpdate,
    MessageResponse,
    ReadingCreate,
    ReadingResponse,
    TelemetryIn,
)

router = APIRouter(tags=["Buoys"])

admin_dependencies = [Depends(verify_admin_token)]

router.add_api_route(
    "/buoys",
    BuoyController.list_buoys,
    methods=["GET"],
    response_model=list[BuoyResponse],
    dependencies=admin_dependencies,
)
router.add_api_route(
    "/buoys/{buoy_id}",
    BuoyController.get_buoy,
    methods=["GET"],
    response_model=BuoyResponse,
    dependencies=admin_dependencies,
)
router.add_api_route(
    "/buoys/{buoy_id}",
    BuoyController.create_buoy,
    methods=["POST"],
    response_model=BuoyResponse,
    dependencies=admin_dependencies,
)
router.add_api_route(
    "/buoys/{buoy_id}",
    BuoyController.update_buoy,
    methods=["PUT"],
    response_model=BuoyResponse,
    dependencies=admin_dependencies,
)
router.add_api_route(
    "/buoys/{buoy_id}",
    BuoyController.delete_buoy,
    methods=["DELETE"],
    response_model=MessageResponse,
    dependencies=admin_dependencies,
)

router.add_api_route(
    "/buoys/{buoy_id}/readings",
    BuoyController.list_readings,
    methods=["GET"],
    response_model=list[ReadingResponse],
    dependencies=admin_dependencies,
)
router.add_api_route(
    "/buoys/{buoy_id}/readings",
    BuoyController.create_reading,
    methods=["POST"],
    response_model=ReadingResponse,
    dependencies=admin_dependencies,
)
router.add_api_route(
    "/buoys/{buoy_id}/readings/{reading_id}",
    BuoyController.get_reading,
    methods=["GET"],
    response_model=ReadingResponse,
    dependencies=admin_dependencies,
)
router.add_api_route(
    "/buoys/{buoy_id}/readings/{reading_id}",
    BuoyController.delete_reading,
    methods=["DELETE"],
    response_model=MessageResponse,
    dependencies=admin_dependencies,
)

router.add_api_route(
    "/telemetry",
    BuoyController.receive_telemetry,
    methods=["POST"],
    response_model=ReadingResponse,
)
