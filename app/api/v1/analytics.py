from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard():
    """Get dashboard analytics. TODO: Implement."""
    return {
        "success": False,
        "error": {
            "code": "NOT_IMPLEMENTED",
            "message": "Analytics not yet implemented. See FASTAPI_ROUTES_EXAMPLES.md for implementation."
        }
    }
