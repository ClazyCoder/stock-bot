import logging
from fastapi import APIRouter, Request
from typing import Optional
from fastapi import Header
import os
from fastapi import HTTPException, Depends
from secrets import compare_digest
from dependencies import get_admin_repository
from db.repositories.admin.admin_repository import AdminRepository
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

_LOCALHOST_ADDRESSES = {"127.0.0.1", "::1", "localhost"}


async def verify_localhost(request: Request):
    """Reject requests that do not originate from localhost.

    Note: This check uses the direct client IP from the TCP connection.
    If this application runs behind a reverse proxy on the same machine,
    configure the proxy to only forward connections from localhost, rather
    than relying on X-Forwarded-For headers which can be spoofed.
    """
    client_host = request.client.host if request.client else None
    if client_host not in _LOCALHOST_ADDRESSES:
        logger.warning(
            f"Admin endpoint access denied for non-local IP: {client_host}"
        )
        raise HTTPException(status_code=403, detail="Access denied: admin endpoints are restricted to localhost")


async def verify_admin_token(admin_token: Optional[str] = Header(None)):
    if admin_token is None:
        raise HTTPException(status_code=403, detail="Access denied")
    env_admin_token = os.getenv("ADMIN_TOKEN")
    if env_admin_token is None:
        logger.error("ADMIN_TOKEN environment variable is not set")
        raise HTTPException(status_code=500, detail="Server misconfigured: ADMIN_TOKEN is not set")
    if not compare_digest(admin_token, env_admin_token):
        raise HTTPException(status_code=403, detail="Access denied")
    return admin_token


class AdminReportRequest(BaseModel):
    query: str = Field(..., description="The query to send to the database")


@router.post("/raw_sql", dependencies=[Depends(verify_localhost), Depends(verify_admin_token)])
async def send_raw_query(request: AdminReportRequest, admin_repository: AdminRepository = Depends(get_admin_repository)):
    result = await admin_repository.send_raw_query(request.query)
    if result is None:
        # Avoid returning 200 OK with a null body when execution fails
        raise HTTPException(status_code=500, detail="Failed to execute raw SQL query")
    return result


@router.get("/health_check", dependencies=[Depends(verify_localhost), Depends(verify_admin_token)])
async def health_check():
    return {"message": "OK"}
