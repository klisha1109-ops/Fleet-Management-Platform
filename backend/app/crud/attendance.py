from datetime import date

from sqlalchemy.orm import Session

from app.models.attendance import Attendance, AttendanceActivityType, AttendanceStatus


def create_activity(db: Session, *, driver_id, activity_type: AttendanceActivityType, trip_id=None, notes: str | None = None, commit: bool = True) -> Attendance:
    activity = Attendance(driver_id=driver_id, activity_type=activity_type, trip_id=trip_id, notes=notes)
    db.add(activity)
    if commit:
        db.commit()
        db.refresh(activity)
    return activity


def get_driver_activity(db: Session, driver_id, limit: int = 50) -> list[Attendance]:
    return db.query(Attendance).filter(Attendance.driver_id == driver_id, Attendance.activity_type.isnot(None)).order_by(Attendance.occurred_at.desc(), Attendance.attendance_id.desc()).limit(limit).all()


def get_open_check_in(db: Session, driver_id) -> Attendance | None:
    latest = db.query(Attendance).filter(Attendance.driver_id == driver_id, Attendance.activity_type.in_([AttendanceActivityType.CheckIn, AttendanceActivityType.CheckOut])).order_by(Attendance.occurred_at.desc(), Attendance.attendance_id.desc()).first()
    return latest if latest and latest.activity_type == AttendanceActivityType.CheckIn else None


def mark_attendance(
    db: Session,
    *,
    driver_id,
    attendance_date: date,
    attendance_status: AttendanceStatus,
    notes: str | None = None,
) -> tuple[Attendance, bool]:
    """Create or correct one driver's daily attendance without touching activities."""
    record = db.query(Attendance).filter(
        Attendance.driver_id == driver_id,
        Attendance.date == attendance_date,
        Attendance.status.isnot(None),
    ).one_or_none()
    created = record is None
    if record is None:
        record = Attendance(driver_id=driver_id, date=attendance_date,
                            status=attendance_status, notes=notes, activity_type=None)
        db.add(record)
    else:
        record.status = attendance_status
        record.notes = notes
    db.commit()
    db.refresh(record)
    return record, created


def get_driver_attendance_history(db: Session, driver_id, start_date: date | None = None,
                                  end_date: date | None = None) -> list[Attendance]:
    query = db.query(Attendance).filter(
        Attendance.driver_id == driver_id,
        Attendance.date.isnot(None),
        Attendance.status.isnot(None),
    )
    if start_date is not None:
        query = query.filter(Attendance.date >= start_date)
    if end_date is not None:
        query = query.filter(Attendance.date <= end_date)
    return query.order_by(Attendance.date.desc(), Attendance.attendance_id.desc()).all()


def get_fleet_attendance(db: Session, start_date: date | None = None,
                         end_date: date | None = None) -> list[Attendance]:
    query = db.query(Attendance).filter(Attendance.date.isnot(None), Attendance.status.isnot(None))
    if start_date is not None:
        query = query.filter(Attendance.date >= start_date)
    if end_date is not None:
        query = query.filter(Attendance.date <= end_date)
    return query.order_by(Attendance.date.desc(), Attendance.driver_id.asc(), Attendance.attendance_id.desc()).all()
