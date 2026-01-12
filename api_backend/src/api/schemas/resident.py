from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ResidentBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=200, description="Resident first name.")
    last_name: str = Field(..., min_length=1, max_length=200, description="Resident last name.")

    address: Optional[str] = Field(None, max_length=500, description="Street address.")
    city: Optional[str] = Field(None, max_length=200, description="City.")
    state: Optional[str] = Field(None, max_length=50, description="State.")
    zip: Optional[str] = Field(None, max_length=20, description="ZIP/postal code.")

    phone: Optional[str] = Field(None, max_length=50, description="Phone number.")
    email: Optional[str] = Field(None, max_length=320, description="Email address.")

    photo_url: Optional[str] = Field(None, max_length=2000, description="Public photo URL.")
    photo_public_id: Optional[str] = Field(None, max_length=500, description="Provider photo public id (e.g., Cloudinary public_id).")

    notes: Optional[str] = Field(None, max_length=5000, description="Free-form notes.")


class ResidentCreate(ResidentBase):
    pass


class ResidentUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=200)
    last_name: Optional[str] = Field(None, min_length=1, max_length=200)

    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=200)
    state: Optional[str] = Field(None, max_length=50)
    zip: Optional[str] = Field(None, max_length=20)

    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=320)

    photo_url: Optional[str] = Field(None, max_length=2000)
    photo_public_id: Optional[str] = Field(None, max_length=500)

    notes: Optional[str] = Field(None, max_length=5000)


class ResidentOut(ResidentBase):
    id: UUID = Field(..., description="Resident id (UUID).")
    created_at: datetime = Field(..., description="Created timestamp.")
    updated_at: datetime = Field(..., description="Last updated timestamp.")


class ResidentListResponse(BaseModel):
    items: list[ResidentOut] = Field(..., description="Page of residents.")
    total: int = Field(..., description="Total number of residents matching the query.")
    page: int = Field(..., description="Current page (1-based).")
    page_size: int = Field(..., description="Items per page.")
