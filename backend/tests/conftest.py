"""Shared pytest fixtures."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.database.session as db_session_module
from app.auth.security import hash_password
from app.common.enums import UserRole
from app.companies.models import Company, CompanySettings
from app.config.settings import Settings
from app.database.base import Base
from app.database.session import get_db
from app.main import create_app
from app.users.models import User


@pytest.fixture
def test_settings(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Settings:
    """Return settings configured for tests."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEBUG", "true")
    upload_dir = tmp_path / "uploads"
    return Settings(
        app_name="ProDrive API",
        app_version="0.1.0",
        environment="test",
        debug=True,
        database_url_override="sqlite+pysqlite:///:memory:",
        redis_url_override="redis://localhost:6379/15",
        log_level="WARNING",
        log_json=False,
        jwt_secret_key="test-secret-key-with-32-byte-minimum-length",
        jwt_access_token_expire_minutes=15,
        jwt_refresh_token_expire_days=7,
        seed_admin_email="admin@example.com",
        seed_admin_password="Admin123!",
        upload_root_dir=str(upload_dir),
        max_logo_size_mb=5,
    )


def seed_test_data(db: Session, settings: Settings) -> tuple[Company, User, User]:
    """Create baseline company and users for auth tests."""
    company = Company(name="Test Transport")
    db.add(company)
    db.commit()
    db.refresh(company)

    company_settings = CompanySettings(company_id=company.id)
    db.add(company_settings)

    admin = User(
        company_id=company.id,
        first_name="Admin",
        last_name="User",
        email=settings.seed_admin_email.lower(),
        password_hash=hash_password(settings.seed_admin_password),
        role=UserRole.ADMIN,
        is_active=True,
    )
    dispatcher = User(
        company_id=company.id,
        first_name="Dispatch",
        last_name="User",
        email="dispatcher@example.com",
        password_hash=hash_password("Dispatch123!"),
        role=UserRole.DISPATCHER,
        is_active=True,
    )
    db.add_all([admin, dispatcher])
    db.commit()
    db.refresh(admin)
    db.refresh(dispatcher)
    return company, admin, dispatcher


@pytest.fixture
def db_engine(test_settings: Settings) -> Generator[Engine]:
    """Create an isolated in-memory database engine."""
    engine = create_engine(
        test_settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine: Engine) -> Generator[Session]:
    """Provide a database session bound to the test engine."""
    session = sessionmaker(
        bind=db_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )()
    yield session
    session.close()


@pytest.fixture
def client(
    test_settings: Settings,
    db_engine: Engine,
) -> Generator[TestClient]:
    """Return a test client with an isolated in-memory database."""
    testing_session_local = sessionmaker(
        bind=db_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    seed_db = testing_session_local()
    try:
        seed_test_data(seed_db, test_settings)
    finally:
        seed_db.close()

    db_session_module._engine = db_engine
    db_session_module.SessionLocal = testing_session_local

    application = create_app(test_settings)

    def override_get_db() -> Generator[Session]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    application.dependency_overrides[get_db] = override_get_db

    with TestClient(application) as test_client:
        yield test_client

    db_session_module._engine = None
    db_session_module.SessionLocal = None


@pytest.fixture
def admin_tokens(client: TestClient, test_settings: Settings) -> dict[str, str]:
    """Return admin access and refresh tokens."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_settings.seed_admin_email,
            "password": test_settings.seed_admin_password,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]
