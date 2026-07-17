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

from app.schemas.auth import ForgotPasswordRequest, VerifyOTPRequest, ResetPasswordRequest, BasicResponse
from app.services.password_reset_service import PasswordResetService

@router.post("/forgot-password", response_model=BasicResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Request a password reset OTP."""
    service = PasswordResetService(db)
    service.process_forgot_password(request.email)
    # Always return success to prevent email enumeration
    return {"success": True, "message": "If that email exists, an OTP has been sent."}

@router.post("/verify-otp", response_model=BasicResponse)
async def verify_otp(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """Verify an OTP for a given email."""
    service = PasswordResetService(db)
    service.verify_otp(request.email, request.otp)
    return {"success": True, "message": "OTP is valid."}

@router.post("/reset-password", response_model=BasicResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset the password using email, OTP, and new password."""
    service = PasswordResetService(db)
    service.reset_password(request.email, request.otp, request.new_password)
    return {"success": True, "message": "Password has been successfully reset."}
