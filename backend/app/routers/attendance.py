from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin_or_fleet_manager
from app.crud.attendance import create_activity, get_driver_activity, get_driver_attendance_history, get_fleet_attendance, get_open_check_in, mark_attendance
from app.crud.driver import get_driver_by_user_id
from app.models.attendance import AttendanceActivityType, AttendanceStatus
from app.models.driver import Driver
from app.schemas.attendance import AttendanceCreate, AttendanceMarkRequest, AttendanceRecordResponse, AttendanceResponse
from database import get_db


router = APIRouter(prefix="/attendance", tags=["Driver Attendance & Activity"])


def current_driver_or_404(db: Session, current_user):
    record = get_driver_by_user_id(db, current_user.user_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found")
    return record[0]


def validate_date_range(start_date: date | None, end_date: date | None) -> None:
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start_date must be earlier than or equal to end_date.")


@router.post("/mark", response_model=AttendanceRecordResponse, status_code=status.HTTP_201_CREATED)
def mark_driver_attendance(payload: AttendanceMarkRequest, db: Session = Depends(get_db), current_user=Depends(require_admin_or_fleet_manager)):
    if db.query(Driver).filter(Driver.driver_id == payload.driver_id).first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    record, _ = mark_attendance(db, driver_id=payload.driver_id, attendance_date=payload.date,
                                attendance_status=AttendanceStatus(payload.status), notes=payload.notes)
    return record


@router.get("/fleet", response_model=list[AttendanceRecordResponse])
def list_fleet_attendance(date_value: date | None = None, start_date: date | None = None,
                          end_date: date | None = None, db: Session = Depends(get_db),
                          current_user=Depends(get_current_user)):
    if current_user.role.value not in {"Admin", "FleetManager", "Dispatcher"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view fleet attendance.")
    if date_value is not None:
        start_date = end_date = date_value
    validate_date_range(start_date, end_date)
    return get_fleet_attendance(db, start_date=start_date, end_date=end_date)


@router.get("/me/history", response_model=list[AttendanceRecordResponse])
def get_my_attendance_history(start_date: date | None = None, end_date: date | None = None,
                              db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role.value != "Driver":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Driver users can access this endpoint.")
    validate_date_range(start_date, end_date)
    driver = current_driver_or_404(db, current_user)
    return get_driver_attendance_history(db, driver.driver_id, start_date, end_date)


@router.get("/driver/{driver_id}/history", response_model=list[AttendanceRecordResponse])
def get_attendance_history_for_driver(driver_id: UUID, start_date: date | None = None,
                                      end_date: date | None = None, db: Session = Depends(get_db),
                                      current_user=Depends(get_current_user)):
    validate_date_range(start_date, end_date)
    if current_user.role.value in {"Admin", "FleetManager", "Dispatcher"}:
        return get_driver_attendance_history(db, driver_id, start_date, end_date)
    if current_user.role.value == "Driver":
        driver = current_driver_or_404(db, current_user)
        if driver.driver_id == driver_id:
            return get_driver_attendance_history(db, driver_id, start_date, end_date)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view this driver's attendance.")


@router.post("/check-in", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def check_in(payload: AttendanceCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role.value != "Driver":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Driver users can check in.")
    driver = current_driver_or_404(db, current_user)
    if get_open_check_in(db, driver.driver_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Driver already has an open check-in.")
    return create_activity(db, driver_id=driver.driver_id, activity_type=AttendanceActivityType.CheckIn, notes=payload.notes)


@router.post("/check-out", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def check_out(payload: AttendanceCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role.value != "Driver":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Driver users can check out.")
    driver = current_driver_or_404(db, current_user)
    if not get_open_check_in(db, driver.driver_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Driver must check in before checking out.")
    return create_activity(db, driver_id=driver.driver_id, activity_type=AttendanceActivityType.CheckOut, notes=payload.notes)


@router.get("/me", response_model=list[AttendanceResponse])
def get_my_activity(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role.value != "Driver":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Driver users can access this endpoint.")
    driver = current_driver_or_404(db, current_user)
    return get_driver_activity(db, driver.driver_id)


@router.get("/driver/{driver_id}", response_model=list[AttendanceResponse])
def get_activity_for_driver(driver_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role.value in {"Admin", "FleetManager", "Dispatcher"}:
        return get_driver_activity(db, driver_id)
    if current_user.role.value == "Driver":
        driver = current_driver_or_404(db, current_user)
        if driver.driver_id == driver_id:
            return get_driver_activity(db, driver_id)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view this driver activity.")
