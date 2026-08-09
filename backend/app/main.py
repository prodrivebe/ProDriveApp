"""FastAPI application factory."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import app.database.session as db_session_module
from app.ai.routes import router as ai_router
from app.auth.routes import router as auth_router
from app.cmr.routes import router as cmr_router
from app.common.handlers import register_exception_handlers
from app.common.routes import router as common_router
from app.companies.routes import router as companies_router
from app.config.logging import configure_logging
from app.config.settings import Settings, get_settings
from app.customers.routes import router as customers_router
from app.database.redis import RedisClient
from app.database.session import (
    dispose_engine,
    init_engine,
    verify_database_connection,
)
from app.drivers.routes import router as drivers_router
from app.fleet.routes import router as fleet_router
from app.notifications.routes import router as notifications_router
from app.order_stops.routes import router as stops_router
from app.order_vehicles.routes import router as order_vehicles_router
from app.orders.routes import router as orders_router
from app.orders.vehicle_routes import router as vehicle_vin_router
from app.completion_checklist.routes import router as completion_checklist_router
from app.order_documents.routes import document_router, router as order_documents_router
from app.photos.routes import photo_router, vehicle_photos_router
from app.vehicle_damage.routes import damage_router, router as vehicle_damage_router
from app.vehicle_photos.routes import photo_router as execution_photo_router
from app.vehicle_photos.routes import router as execution_vehicle_photos_router
from app.vin_verification.routes import router as vin_verification_router
from app.reports.routes import router as reports_router
from app.search.routes import router as search_router
from app.realtime.event_service import init_event_service
from app.realtime.routes import router as realtime_router
from app.realtime.websocket_routes import router as realtime_ws_router
from app.trailers.routes import router as trailers_router
from app.trucks.routes import router as trucks_router
from app.users.routes import router as users_router

logger = logging.getLogger(__name__)


async def _realtime_maintenance_loop(interval_seconds: int = 60) -> None:
    """Periodic stale connection cleanup."""
    from app.realtime.event_service import get_event_service

    while True:
        await asyncio.sleep(interval_seconds)
        service = get_event_service()
        if service is not None:
            await service.maintenance()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    app_settings = settings or get_settings()
    configure_logging(app_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("Starting ProDrive API in %s", app_settings.environment)
        engine_initialized_in_lifespan = False
        if db_session_module._engine is None:
            init_engine(app_settings)
            verify_database_connection()
            engine_initialized_in_lifespan = True
        redis_client = RedisClient(app_settings)
        app.state.redis_client = redis_client
        use_memory_bridge = app_settings.environment == "test"
        event_service = init_event_service(
            redis_client=None if use_memory_bridge else redis_client.client,
            use_memory_bridge=use_memory_bridge,
        )
        event_service.bind_loop(asyncio.get_running_loop())
        event_service.start()
        app.state.event_service = event_service
        maintenance_task = asyncio.create_task(_realtime_maintenance_loop())
        yield
        maintenance_task.cancel()
        event_service.stop()
        redis_client.close()
        if engine_initialized_in_lifespan:
            dispose_engine()
        logger.info("Stopped ProDrive API")

    application = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        description="ProDrive vehicle transport management platform API.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    register_exception_handlers(application)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(
        common_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        auth_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        companies_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        users_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        drivers_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        trucks_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        trailers_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        fleet_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        customers_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        orders_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        stops_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        order_vehicles_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        vehicle_vin_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        vin_verification_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        execution_vehicle_photos_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        execution_photo_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        vehicle_damage_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        damage_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        order_documents_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        document_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        completion_checklist_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        ai_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        cmr_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        vehicle_photos_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        photo_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        notifications_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        reports_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        search_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        realtime_router,
        prefix=app_settings.api_v1_prefix,
    )
    application.include_router(
        realtime_ws_router,
        prefix=app_settings.api_v1_prefix,
    )

    upload_root = Path(app_settings.upload_root_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    application.mount("/uploads", StaticFiles(directory=upload_root), name="uploads")

    application.dependency_overrides[get_settings] = lambda: app_settings

    return application
