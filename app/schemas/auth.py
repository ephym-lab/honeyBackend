from pydantic import BaseModel, EmailStr
from typing import Optional


class Register(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class Login(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str



class UserResponse(BaseModel):
    id: str
    email: str
    role: str

class RegisterData(BaseModel):
    user: UserResponse

class TokenData(BaseModel):
    token: str
    user: UserResponse


class TokenResponse(BaseModel):
    success: bool = True
    data: TokenData

class RegisterResponse(BaseModel):
    success: bool = True# "token": access_token,
    data: RegisterData
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

class BasicResponse(BaseModel):
    success: bool
    message: str
