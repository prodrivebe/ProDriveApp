"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.auth.routes import router as auth_router
from app.common.handlers import register_exception_handlers
from app.common.routes import router as common_router
from app.ai.routes import router as ai_router
from app.cmr.routes import router as cmr_router
from app.companies.routes import router as companies_router
from app.customers.routes import router as customers_router
from app.drivers.routes import router as drivers_router
from app.fleet.routes import router as fleet_router
from app.notifications.routes import router as notifications_router
from app.orders.routes import router as orders_router
from app.orders.stop_routes import router as stops_router
from app.orders.vehicle_routes import router as vehicles_router
from app.photos.routes import photo_router, vehicle_photos_router
from app.reports.routes import router as reports_router
from app.search.routes import router as search_router
from app.trailers.routes import router as trailers_router
from app.trucks.routes import router as trucks_router
from app.users.routes import router as users_router
from app.config.cors import configure_cors
from app.config.logging import configure_logging
from app.config.settings import Settings, get_settings
from app.database.redis import RedisClient
from app.database.session import dispose_engine, get_db, init_engine, verify_database_connection
import app.database.session as db_session_module

logger = logging.getLogger(__name__)


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
        yield
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
    configure_cors(application, app_settings)

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
        vehicles_router,
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

    upload_root = Path(app_settings.upload_root_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    application.mount("/uploads", StaticFiles(directory=upload_root), name="uploads")

    application.dependency_overrides[get_settings] = lambda: app_settings

    return application
