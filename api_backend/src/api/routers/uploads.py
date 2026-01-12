from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.api.core.config import settings

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post(
    "/cloudinary/sign",
    summary="Cloudinary upload stub",
    description=(
        "Stub endpoint for future Cloudinary integration.\n\n"
        "Environment variables reserved for future use:\n"
        "- CLOUDINARY_CLOUD_NAME\n"
        "- CLOUDINARY_API_KEY\n"
        "- CLOUDINARY_API_SECRET\n\n"
        "This endpoint currently returns 501 to indicate it's not implemented yet."
    ),
    operation_id="uploads_cloudinary_stub",
)
def cloudinary_upload_stub() -> dict:
    """Stub for Cloudinary upload signing/handshake (not implemented yet)."""
    # We reference settings so configuration is validated/available for later work.
    _ = (settings.cloudinary_cloud_name, settings.cloudinary_api_key, settings.cloudinary_api_secret)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Cloudinary upload integration is not implemented yet.",
    )
