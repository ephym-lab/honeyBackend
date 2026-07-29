import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.password_reset import PasswordReset
from app.core.security import get_password_hash

class PasswordResetService:
    def __init__(self, db: Session):
        self.db = db

    def generate_otp(self) -> str:
        """Generate a 6-digit numeric OTP."""
        return str(random.randint(100000, 999999))

    def process_forgot_password(self, email: str) -> None:
        """Process forgot password request."""
        # Find user
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # We don't want to leak whether the user exists or not
            return
            
        # Delete any existing OTPs for this user to ensure only the latest is valid
        self.db.query(PasswordReset).filter(PasswordReset.email == email).delete()
        
        # Create new OTP
        otp = self.generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        reset_record = PasswordReset(
            email=email,
            otp=otp,
            expires_at=expires_at
        )
        self.db.add(reset_record)
        self.db.commit()
        
        # Send actual email
        from app.services.email_service import EmailService
        from app.services.email_templates import EmailTemplates
        
        email_service = EmailService()
        customer_name = user.full_name or "Valued Customer"
        html_body = EmailTemplates.password_reset_otp(
            customer_name=customer_name,#type:ignore
            otp=otp,
            expires_in_minutes=10
        )
        
        email_service.send_html_email(
            to_email=email,
            subject="Your Password Reset Code",
            html_body=html_body
        )
    def verify_otp(self, email: str, otp: str) -> bool:
        """Verify if an OTP is valid for the given email."""
        reset_record = self.db.query(PasswordReset).filter(
            PasswordReset.email == email,
            PasswordReset.otp == otp
        ).first()
        
        if not reset_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP."
            )
            
        if reset_record.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired. Please request a new one."
            )
            
        return True

    def reset_password(self, email: str, otp: str, new_password: str) -> None:
        """Reset the user's password using the OTP."""
        # First verify the OTP
        self.verify_otp(email, otp)
        
        # Find user
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
            
        # Update password
        user.password_hash = get_password_hash(new_password)  # type: ignore
        
        # Delete the OTP record so it can't be used again
        self.db.query(PasswordReset).filter(PasswordReset.email == email).delete()
        
        self.db.commit()
