from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, get_password_hash, verify_password
from app.models.entities import User, UserRole
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.schemas.common import APIResponse, HealthCheckResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth & RBAC"])
DUMMY_HASH = get_password_hash("unused-password-for-timing")


def check_origin(request: Request):
    origin = request.headers.get("origin")
    if origin and origin not in settings.BACKEND_CORS_ORIGINS:
        raise HTTPException(403, "Nguồn yêu cầu không được phép.")
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Nguồn yêu cầu không được phép.")


def set_tokens(response: Response, user: User):
    now = datetime.now(timezone.utc)
    access = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh = jwt.encode(
        {"sub": str(user.id), "type": "refresh", "jti": str(uuid4()),
         "iat": now, "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )
    for name, value, age, path in [
        ("access_token", access, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, settings.API_V1_STR),
        ("refresh_token", refresh, settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, f"{settings.API_V1_STR}/auth"),
    ]:
        response.set_cookie(name, value, max_age=age, httponly=True,
                            secure=settings.COOKIE_SECURE, samesite="lax", path=path)
    response.headers["Cache-Control"] = "no-store"


@router.get("/health", response_model=HealthCheckResponse)
def health():
    return HealthCheckResponse(service="Auth & RBAC Service")


@router.post("/register", status_code=201, response_model=APIResponse[UserResponse], dependencies=[Depends(check_origin)])
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "Email đã được sử dụng.")
    user = User(email=email, full_name=payload.full_name,
                password_hash=get_password_hash(payload.password), role=UserRole.STUDENT)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Không thể tạo tài khoản. Email có thể đã được sử dụng.")
    db.refresh(user)
    return APIResponse[UserResponse](message="Đăng ký thành công. Vui lòng đăng nhập.", data=user)


@router.post("/login", response_model=APIResponse[UserResponse], dependencies=[Depends(check_origin)])
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(payload.email).lower()).first()
    password = payload.password
    oversized = len(password.encode("utf-8")) > 72
    valid = verify_password("" if oversized else password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid or not user.is_active or oversized:
        raise HTTPException(401, "Email hoặc mật khẩu không đúng.")
    set_tokens(response, user)
    return APIResponse[UserResponse](message="Đăng nhập thành công.", data=user)


@router.post("/refresh", response_model=APIResponse[UserResponse], dependencies=[Depends(check_origin)])
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(request.cookies.get("refresh_token", ""), settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM], options={"require": ["exp", "sub", "type", "jti"]})
        if payload["type"] != "refresh":
            raise ValueError()
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError, TypeError, AttributeError):
        raise HTTPException(401, "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(401, "Phiên đăng nhập không hợp lệ.")
    set_tokens(response, user)
    return APIResponse[UserResponse](data=user)


@router.post("/logout", dependencies=[Depends(check_origin)])
def logout(response: Response):
    response.delete_cookie("access_token", path=settings.API_V1_STR)
    response.delete_cookie("refresh_token", path=f"{settings.API_V1_STR}/auth")
    response.headers["Cache-Control"] = "no-store"
    return APIResponse(message="Đã đăng xuất.")


@router.get("/me", response_model=APIResponse[UserResponse])
def me(response: Response, user: User = Depends(get_current_user)):
    response.headers["Cache-Control"] = "no-store"
    return APIResponse[UserResponse](data=user)
