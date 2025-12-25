from fastapi import APIRouter

router = APIRouter(tags=["download"])

@router.get("/download/dummy")
async def download_dummy():
    return {"status": "ok"}
