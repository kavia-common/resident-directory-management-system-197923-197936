from __future__ import annotations

from typing import Annotated, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from src.api.db.session import get_db
from src.api.deps.auth import get_current_user, require_admin
from src.api.models.resident import Resident
from src.api.models.user import User
from src.api.schemas.resident import ResidentCreate, ResidentListResponse, ResidentOut, ResidentUpdate

router = APIRouter(prefix="/residents", tags=["residents"])


def _to_out(r: Resident) -> ResidentOut:
    return ResidentOut(
        id=r.id,
        first_name=r.first_name,
        last_name=r.last_name,
        address=r.address,
        city=r.city,
        state=r.state,
        zip=r.zip,
        phone=r.phone,
        email=r.email,
        photo_url=r.photo_url,
        photo_public_id=r.photo_public_id,
        notes=r.notes,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.get(
    "",
    response_model=ResidentListResponse,
    summary="Search/list residents",
    description="Search residents by name/address/contact fields with pagination and sorting.",
    operation_id="residents_list",
)
def list_residents(
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    q: Optional[str] = Query(None, description="Search query matched against name/address/phone/email/city/state/zip."),
    page: int = Query(1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(20, ge=1, le=100, description="Page size (max 100)."),
    sort_by: Literal["last_name", "first_name", "created_at", "updated_at", "city"] = Query(
        "last_name", description="Sort field."
    ),
    sort_dir: Literal["asc", "desc"] = Query("asc", description="Sort direction."),
) -> ResidentListResponse:
    """List residents with search, pagination, and sorting."""
    base = select(Resident)

    if q and q.strip():
        like = f"%{q.strip()}%"
        base = base.where(
            or_(
                Resident.first_name.ilike(like),
                Resident.last_name.ilike(like),
                Resident.address.ilike(like),
                Resident.city.ilike(like),
                Resident.state.ilike(like),
                Resident.zip.ilike(like),
                Resident.phone.ilike(like),
                Resident.email.ilike(like),
            )
        )

    sort_col = {
        "last_name": Resident.last_name,
        "first_name": Resident.first_name,
        "created_at": Resident.created_at,
        "updated_at": Resident.updated_at,
        "city": Resident.city,
    }[sort_by]

    ordering = asc(sort_col) if sort_dir == "asc" else desc(sort_col)

    # Total count
    total_stmt = select(func.count()).select_from(base.subquery())
    total = int(db.execute(total_stmt).scalar_one())

    stmt = base.order_by(ordering).offset((page - 1) * page_size).limit(page_size)
    items = db.execute(stmt).scalars().all()

    return ResidentListResponse(
        items=[_to_out(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{resident_id}",
    response_model=ResidentOut,
    summary="Get resident",
    description="Fetch a resident by id.",
    operation_id="residents_get",
)
def get_resident(
    resident_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> ResidentOut:
    """Get a resident by id."""
    resident = db.get(Resident, resident_id)
    if resident is None:
        raise HTTPException(status_code=404, detail="Resident not found")
    return _to_out(resident)


@router.post(
    "",
    response_model=ResidentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create resident (admin)",
    description="Create a new resident record. Admin-only.",
    operation_id="residents_create",
)
def create_resident(
    payload: ResidentCreate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> ResidentOut:
    """Create a resident (admin only)."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    resident = Resident(
        first_name=payload.first_name,
        last_name=payload.last_name,
        address=payload.address,
        city=payload.city,
        state=payload.state,
        zip=payload.zip,
        phone=payload.phone,
        email=payload.email,
        photo_url=payload.photo_url,
        photo_public_id=payload.photo_public_id,
        notes=payload.notes,
        created_at=now,
        updated_at=now,
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)
    return _to_out(resident)


@router.put(
    "/{resident_id}",
    response_model=ResidentOut,
    summary="Update resident (admin)",
    description="Update a resident record. Admin-only.",
    operation_id="residents_update",
)
def update_resident(
    resident_id: UUID,
    payload: ResidentUpdate,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> ResidentOut:
    """Update a resident (admin only)."""
    resident = db.get(Resident, resident_id)
    if resident is None:
        raise HTTPException(status_code=404, detail="Resident not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(resident, field, value)

    from datetime import datetime, timezone
    resident.updated_at = datetime.now(timezone.utc)

    db.add(resident)
    db.commit()
    db.refresh(resident)
    return _to_out(resident)


@router.delete(
    "/{resident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete resident (admin)",
    description="Delete a resident record. Admin-only.",
    operation_id="residents_delete",
)
def delete_resident(
    resident_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> None:
    """Delete a resident (admin only)."""
    resident = db.get(Resident, resident_id)
    if resident is None:
        raise HTTPException(status_code=404, detail="Resident not found")

    db.delete(resident)
    db.commit()
    return None
