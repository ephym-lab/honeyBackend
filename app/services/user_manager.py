from abc import ABC
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from datetime import timedelta

from app.schemas.auth import Register, Login
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.config import settings


class UserManagerService(ABC):
    """Abstract base class for user management services."""
    
    def __init__(self, db: Session):
        self.db = db


class RegisterService(UserManagerService):
    """Service for handling user registration."""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def register_user(self, user_data: Register):
        """
        Register a new user.
        
        Args:
            user_data: Registration data containing email, password, and optional full_name
            
        Returns:
            dict: Success response with user data and access token
            
        Raises:
            HTTPException: If email already exists or registration fails
        """
        self.user_data = user_data
        
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        try:
            # Create new user
            new_user = User(
                email=user_data.email,
                password_hash=hash_password(user_data.password),
                full_name=user_data.full_name,
                role="customer"  # Default role for new registrations
            )
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            # Create access token
            # access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            # access_token = create_access_token(
            #     data={"sub": str(new_user.id), "email": new_user.email, "role": new_user.role},
            #     expires_delta=access_token_expires
            # )
            
            return {
                "success": True,
                "data": {
                    "user": {
                        "id": str(new_user.id),
                        "email": new_user.email,
                        "role": new_user.role,
                        "full_name": new_user.full_name
                    }
                }
            }
            
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed. Please try again."
            )
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred during registration: {str(e)}"
            )


class LoginService(UserManagerService):
    """Service for handling user login."""
    
    def __init__(self, db: Session):
        super().__init__(db)

    def login_user(self, user_data: Login):
        """
        Authenticate and login a user.
        
        Args:
            user_data: Login credentials containing email and password
            
        Returns:
            dict: Success response with user data and access token
            
        Raises:
            HTTPException: If credentials are invalid
        """
        self.user_data = user_data
        
        # Find user by email
        user = self.db.query(User).filter(User.email == user_data.email).first()
        
        if not user or not verify_password(user_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role},
            expires_delta=access_token_expires
        )
        
        return {
            "success": True,
            "data": {
                "token": access_token,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "role": user.role,
                    "full_name": getattr(user, 'full_name', None)
                }
            }
        }
