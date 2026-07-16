from fastapi import APIRouter

router = APIRouter()


@router.post("/mpesa/callback")
async def mpesa_callback():
    """Handle M-Pesa payment callback. TODO: Implement."""
    return {"ResultCode": 0, "ResultDesc": "Accepted"}
