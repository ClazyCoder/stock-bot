import logging
from fastapi import APIRouter
from typing import Optional
from fastapi import Header
import os
from fastapi import HTTPException, Depends
from secrets import compare_digest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


async def verify_admin_token(admin_token: Optional[str] = Header(None)):
    if admin_token is None:
        raise HTTPException(status_code=403, detail="Access denied")
    if not compare_digest(admin_token, os.getenv("ADMIN_TOKEN")):
        raise HTTPException(status_code=403, detail="Access denied")
    return admin_token


@router.get("/", dependencies=[Depends(verify_admin_token)])
async def get_admin():
    return {"message": "Admin access granted"}
