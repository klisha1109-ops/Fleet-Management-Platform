from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import RoleEnum, User
from app.schemas.user import UserCreate, UserManagementCreate, UserManagementUpdate
from app.core.security import hash_password, verify_password


def get_user_by_email(db: Session, email: str):
    """
    Retrieve a user by email.
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id):
    return db.query(User).filter(User.user_id == user_id).first()


def get_users(
    db: Session,
    *,
    skip: int,
    limit: int,
    search: str | None = None,
    role=None,
    is_active: bool | None = None,
):
    query = db.query(User)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            User.full_name.ilike(pattern)
            | User.email.ilike(pattern)
            | User.phone.ilike(pattern)
        )
    if role is not None:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    total = query.count()
    items = query.order_by(User.created_at.desc(), User.full_name.asc()).offset(skip).limit(limit).all()
    return items, total


def email_in_use(db: Session, email: str, *, excluding_user_id=None) -> bool:
    query = db.query(User).filter(func.lower(User.email) == email.lower())
    if excluding_user_id is not None:
        query = query.filter(User.user_id != excluding_user_id)
    return query.first() is not None


def create_managed_user(db: Session, user: UserManagementCreate):
    db_user = User(
        full_name=user.full_name.strip(),
        email=user.email.lower(),
        password=hash_password(user.password),
        phone=user.phone,
        address=user.address,
        role=user.role,
        email_verified=True,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_managed_user(db: Session, user: User, changes: UserManagementUpdate):
    for field, value in changes.model_dump(exclude_unset=True).items():
        if field == "email" and value is not None:
            value = value.lower()
        if field == "full_name" and value is not None:
            value = value.strip()
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def set_user_active_status(db: Session, user: User, is_active: bool):
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def active_admin_count(db: Session) -> int:
    return db.query(User).filter(User.role == RoleEnum.Admin, User.is_active.is_(True)).count()


def create_user(db: Session, user: UserCreate):
    """
    Create a new user with a hashed password.
    """

    hashed_pw = hash_password(user.password)

    db_user = User(
        full_name=user.full_name,
        email=user.email,
        password=hashed_pw,
        phone=user.phone,
        role=user.role
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def authenticate_user(db: Session, email: str, password: str):
    """
    Authenticate a user during login.
    """

    user = get_user_by_email(db, email)

    if not user:
        return None

    if not verify_password(password, user.password):
        return None

    return user
def update_user_profile(db: Session, user: User, full_name: str, phone: str | None):
    user.full_name = full_name
    user.phone = phone

    db.commit()
    db.refresh(user)

    return user


def update_user_email(db: Session, user: User, email: str):
    user.email = email

    db.commit()
    db.refresh(user)

    return user


def update_user_password(db: Session, user: User, new_password: str):
    user.password = hash_password(new_password)

    db.commit()
    db.refresh(user)

    return user


def set_verification_code(
    db: Session,
    user: User,
    code_hash: str,
    expires_at: datetime,
):
    user.email_verified = False
    user.verification_code_hash = code_hash
    user.verification_code_expires_at = expires_at
    db.commit()
    db.refresh(user)
    return user


def verify_user_email(db: Session, user: User):
    user.email_verified = True
    user.verification_code_hash = None
    user.verification_code_expires_at = None
    db.commit()
    db.refresh(user)
    return user
