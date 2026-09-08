import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class AttendanceActivityType(str, enum.Enum):
    TripStarted = "Trip Started"
    TripCompleted = "Trip Completed"
    CheckIn = "Attendance / Check-in"
    CheckOut = "Attendance / Check-out"


class AttendanceStatus(str, enum.Enum):
    Present = "Present"
    Leave = "Leave"
    Absent = "Absent"


class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    driver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drivers.driver_id"),
        nullable=True,
    )

    activity_type = Column(
        Enum(
            AttendanceActivityType,
            name="attendance_activity_type",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=True,
    )

    occurred_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    trip_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trips.trip_id"),
        nullable=True,
    )

    notes = Column(
        String(500),
        nullable=True,
    )

    # Daily attendance is separate from the existing activity stream.  Trip
    # and check-in/out activity rows leave these fields NULL.
    date = Column(Date, nullable=True)
    status = Column(
        Enum(
            AttendanceStatus,
            name="attendance_status",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=True,
    )
