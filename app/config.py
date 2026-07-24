from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # API
    API_V1_PREFIX: str = "/v1"
    PROJECT_NAME: str = "Premium Honey API"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # CORS
    BACKEND_CORS_ORIGINS: str = '["http://localhost:3000"]'
    
    @property
    def cors_origins(self) -> List[str]:
        return json.loads(self.BACKEND_CORS_ORIGINS)
    

    # Email
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    EMAIL_FROM_NAME: str = "HoneyBiz"
    ADMIN_EMAIL: str = ""
    
    # Admin
    DEFAULT_ADMIN_EMAIL: str = ""
    DEFAULT_ADMIN_PASSWORD: str = ""
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_BUCKET_NAME: str = "HoneyBiz"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()