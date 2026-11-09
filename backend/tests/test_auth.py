import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.config import Settings, settings
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.entities import User


@pytest.fixture
def session(auth_engine):
    with auth_engine.connect() as connection:
        transaction = connection.begin()
        if connection.dialect.name == "sqlite":
            connection.exec_driver_sql("BEGIN")
        try:
            with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
                app.dependency_overrides[get_db] = lambda: db
                yield db
        finally:
            app.dependency_overrides.clear()
            transaction.rollback()


@pytest.fixture
def client(session):
    with TestClient(app) as client:
        yield client


ACCOUNT = {"email": "Student@example.com", "full_name": "Nguyễn An", "password": "Password123!"}


@pytest.mark.parametrize("origins", [
    ["http://localhost:5173/"],
    "http://localhost:5173/",
    '["http://localhost:5173/"]',
])
def test_origin_configuration_normalization(client, monkeypatch, origins):
    config = Settings(_env_file=None, BACKEND_CORS_ORIGINS=origins)
    assert config.BACKEND_CORS_ORIGINS == ["http://localhost:5173"]
    monkeypatch.setattr(settings, "BACKEND_CORS_ORIGINS", config.BACKEND_CORS_ORIGINS)
    headers = {"Origin": "http://localhost:5173"}
    assert client.post("/api/v1/auth/register", json=ACCOUNT, headers=headers).status_code == 201
    assert client.post("/api/v1/auth/login", json=ACCOUNT, headers=headers).status_code == 200
    assert client.post("/api/v1/auth/refresh", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/login", json=ACCOUNT,
                       headers={"Origin": "https://evil.example"}).status_code == 403


def test_registration_hash_and_duplicate(client, session):
    response = client.post("/api/v1/auth/register", json=ACCOUNT)
    assert response.status_code == 201, response.text
    assert response.json()["data"]["role"] == "STUDENT"
    assert "password" not in response.text
    user = session.query(User).one()
    assert user.password_hash.startswith("$2b$")
    assert user.password_hash != ACCOUNT["password"]
    assert verify_password(ACCOUNT["password"], user.password_hash)
    assert user.email == "student@example.com"
    assert client.post("/api/v1/auth/register", json=ACCOUNT).status_code == 409
    assert client.post("/api/v1/auth/register", json={**ACCOUNT, "role": "ADMIN"}).status_code == 422


@pytest.mark.parametrize("role", ["STUDENT", "INSTRUCTOR"])
def test_registration_selected_role_persists_through_login(client, session, role):
    response = client.post("/api/v1/auth/register", json={**ACCOUNT, "role": role})
    assert response.status_code == 201, response.text
    assert response.json()["data"]["role"] == role
    assert session.query(User).one().role.value == role
    assert client.post("/api/v1/auth/login", json=ACCOUNT).status_code == 200
    assert client.get("/api/v1/auth/me").json()["data"]["role"] == role


@pytest.mark.parametrize("role", ["ADMIN", "TEACHER", "", None])
def test_registration_rejects_invalid_roles(client, session, role):
    response = client.post("/api/v1/auth/register", json={**ACCOUNT, "role": role})
    assert response.status_code == 422
    assert session.query(User).count() == 0


def test_login_cookies_refresh_and_logout(client):
    client.post("/api/v1/auth/register", json=ACCOUNT)
    response = client.post("/api/v1/auth/login", json=ACCOUNT)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert all("HttpOnly" in value and "SameSite=lax" in value for value in response.headers.get_list("set-cookie"))
    access = client.cookies.get("access_token")
    refresh = client.cookies.get("refresh_token")
    for token, kind in [(access, "access"), (refresh, "refresh")]:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["type"] == kind
        assert payload["exp"] > datetime.now(timezone.utc).timestamp()
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh}"}).status_code == 401
    assert client.post("/api/v1/auth/refresh").status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_credentials_validation_and_origin(client, session):
    client.post("/api/v1/auth/register", json=ACCOUNT)
    for credentials in [{**ACCOUNT, "password": "incorrect"}, {**ACCOUNT, "email": "missing@example.com"}, {**ACCOUNT, "password": "a" * 73}]:
        response = client.post("/api/v1/auth/login", json=credentials)
        assert response.status_code == 401
        assert response.json()["detail"] == "Email hoặc mật khẩu không đúng."
    for changes in [{"email": "bad"}, {"password": "short"}, {"password": "ế" * 30}, {"full_name": "   "}]:
        assert client.post("/api/v1/auth/register", json={**ACCOUNT, **changes}).status_code == 422
    assert client.post("/api/v1/auth/login", json=ACCOUNT, headers={"Origin": "https://evil.example"}).status_code == 403
    user = session.query(User).one()
    user.is_active = False
    session.commit()
    assert client.post("/api/v1/auth/login", json=ACCOUNT).status_code == 401


def test_expired_tampered_and_wrong_purpose_tokens(client, session):
    client.post("/api/v1/auth/register", json=ACCOUNT)
    user = session.query(User).one()
    for token in ["invalid", jwt.encode({"sub": str(user.id), "type": "refresh", "jti": "test", "exp": datetime.now(timezone.utc) - timedelta(seconds=1)}, settings.SECRET_KEY, algorithm=settings.ALGORITHM), create_access_token({"sub": str(user.id)})]:
        client.cookies.set("refresh_token", token)
        assert client.post("/api/v1/auth/refresh").status_code == 401
    expired = create_access_token({"sub": str(user.id)}, timedelta(seconds=-1))
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    malformed = create_access_token({"sub": "not-a-uuid"})
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {malformed}"}).status_code == 401


def test_secure_cookie_setting(client, monkeypatch):
    client.post("/api/v1/auth/register", json=ACCOUNT)
    monkeypatch.setattr(settings, "COOKIE_SECURE", True)
    response = client.post("/api/v1/auth/login", json=ACCOUNT)
    assert response.status_code == 200
    assert all("Secure" in cookie for cookie in response.headers.get_list("set-cookie"))


@pytest.mark.parametrize("path", [
    "/api/v1/parser/upload",
    "/api/v1/ai-generator/generate-by-matrix",
    "/api/v1/ai-generator/generate-from-context",
])
@pytest.mark.parametrize("role,expected", [(None, 401), ("STUDENT", 403), ("INSTRUCTOR", 200), ("ADMIN", 200)])
def test_management_api_role_matrix(client, session, path, role, expected):
    from app.models.entities import UserRole
    headers = {}
    if role:
        user = User(email="role@example.com", full_name="Role User", password_hash="unused", role=UserRole(role))
        session.add(user)
        session.flush()
        # The database role is authoritative even if the JWT claims ADMIN.
        headers["Authorization"] = "Bearer " + create_access_token({"sub": str(user.id), "role": "ADMIN"})
    assert client.post(path, headers=headers).status_code == expected


@pytest.mark.parametrize("role", ["STUDENT", "INSTRUCTOR", "ADMIN"])
def test_profile_data_for_every_role_and_disabled_account(client, session, role):
    from app.models.entities import UserRole
    user = User(email="profile@example.com", full_name="Nguyễn An", password_hash="private-hash", role=UserRole(role))
    session.add(user)
    session.flush()
    headers = {"Authorization": "Bearer " + create_access_token({"sub": str(user.id)})}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert (data["full_name"], data["email"], data["role"]) == (user.full_name, user.email, role)
    assert "password_hash" not in data
    user.is_active = False
    session.flush()
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
