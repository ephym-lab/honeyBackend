from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class NewsletterSubscribe(BaseModel):
    email: EmailStr


class NewsletterResponse(BaseModel):
    success: bool = True
    message: str


class NewsletterBroadcast(BaseModel):
    subject: str
    html_body: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "New Honey Collection Launch! 🍯",
                "html_body": "<h1>Check out our new collection</h1><p>Beautiful honey and equipment...</p>"
            }
        }


class NewsletterBroadcastResponse(BaseModel):
    success: bool = True
    message: str
    emails_sent: int
    failed_emails: List[str] = []
