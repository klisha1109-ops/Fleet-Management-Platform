from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.crud.user import (
    active_admin_count,
    create_managed_user,
    email_in_use,
    get_user_by_id,
    get_users,
    set_user_active_status,
    update_managed_user,
)
from app.models.user import RoleEnum, User
from app.schemas.user import (
    UserListResponse,
    UserManagementCreate,
    UserManagementResponse,
    UserManagementUpdate,
    UserStatusUpdate,
)
from database import get_db


router = APIRouter(prefix="/users", tags=["User Management"])


def user_or_404(db: Session, user_id: UUID) -> User:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def ensure_not_last_active_admin(db: Session, user: User, *, losing_admin: bool) -> None:
    if user.role == RoleEnum.Admin and user.is_active and losing_admin and active_admin_count(db) <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The last active Administrator cannot be deactivated or reassigned.",
        )


@router.get("", response_model=UserListResponse)
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(default=None, max_length=100),
    role: RoleEnum | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    items, total = get_users(db, skip=skip, limit=limit, search=search, role=role, is_active=is_active)
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/{user_id}", response_model=UserManagementResponse)
def read_user(user_id: UUID, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    return user_or_404(db, user_id)


@router.post("", response_model=UserManagementResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserManagementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    if email_in_use(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return create_managed_user(db, payload)


@router.put("/{user_id}", response_model=UserManagementResponse)
def edit_user(
    user_id: UUID,
    payload: UserManagementUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    user = user_or_404(db, user_id)
    if payload.email and email_in_use(db, payload.email, excluding_user_id=user.user_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if payload.role is not None and payload.role != user.role:
        ensure_not_last_active_admin(db, user, losing_admin=True)
    return update_managed_user(db, user, payload)


@router.patch("/{user_id}/status", response_model=UserManagementResponse)
def change_user_status(
    user_id: UUID,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    user = user_or_404(db, user_id)
    if not payload.is_active:
        ensure_not_last_active_admin(db, user, losing_admin=True)
    return set_user_active_status(db, user, payload.is_active)
