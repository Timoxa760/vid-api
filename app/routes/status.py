from fastapi import APIRouter

router = APIRouter(tags=["status"])

@router.get("/status/dummy")
async def status_dummy():
    return {"status": "ok"}
