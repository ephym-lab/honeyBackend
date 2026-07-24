from pydantic import BaseModel

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str
