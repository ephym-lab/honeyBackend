from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, Register, Login,RegisterResponse
from app.core.security import verify_password, create_access_token
from app.config import settings
from app.services.user_manager import RegisterService, LoginService

router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
async def register(
    user_data: Register,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    register_service = RegisterService(db)
    return register_service.register_user(user_data)


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: Login,
    db: Session = Depends(get_db)
):
    """User login using the new service architecture."""
    login_service = LoginService(db)
    return login_service.login_user(credentials)


@router.post("/admin/login", response_model=TokenResponse)
async def admin_login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """Admin login (legacy endpoint)."""
    # Convert LoginRequest to Login schema
    login_data = Login(email=credentials.email, password=credentials.password)
    login_service = LoginService(db)
    return login_service.login_user(login_data)
