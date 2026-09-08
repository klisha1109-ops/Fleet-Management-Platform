"""Integration coverage for management-marked daily attendance."""
import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.deps import get_current_user
from app.models.driver import Driver, DriverStatus
from app.models.user import RoleEnum, User
from database import Base, get_db
from main import app


class AttendanceTrackingIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        cls.Session = sessionmaker(bind=cls.engine, autocommit=False, autoflush=False, expire_on_commit=False)
        def override_db():
            db = cls.Session()
            try: yield db
            finally: db.close()
        def override_user(): return cls.current_user
        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = override_user
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear(); cls.client.close(); Base.metadata.drop_all(bind=cls.engine); cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine); Base.metadata.create_all(bind=self.engine)
        self.admin = self.make_user("admin", RoleEnum.Admin)
        self.manager = self.make_user("manager", RoleEnum.FleetManager)
        self.dispatcher = self.make_user("dispatcher", RoleEnum.Dispatcher)
        self.driver_user = self.make_user("driver", RoleEnum.Driver)
        self.other_driver_user = self.make_user("other", RoleEnum.Driver)
        self.driver = self.make_driver(self.driver_user, "001")
        self.other_driver = self.make_driver(self.other_driver_user, "002")
        self.set_role(self.admin)

    def make_user(self, name, role):
        db = self.Session(); user = User(full_name=name.title(), email=f"{name}@attendance.test", password="hash", phone="9000000000", role=role, email_verified=True); db.add(user); db.commit(); db.refresh(user); db.close(); return user

    def make_driver(self, user, suffix):
        db = self.Session(); driver = Driver(user_id=user.user_id, full_name=user.full_name, license_number=f"AT-{suffix}", status=DriverStatus.Available); db.add(driver); db.commit(); db.refresh(driver); db.close(); return driver

    def set_role(self, user):
        type(self).current_user = SimpleNamespace(user_id=user.user_id, role=user.role, email=user.email)

    @staticmethod
    def payload(driver, attendance_status="Present", day="2026-08-30"):
        return {"driver_id": str(driver.driver_id), "date": day, "status": attendance_status, "notes": "Roster updated"}

    def test_management_can_mark_and_correct_attendance(self):
        self.assertEqual(self.client.post("/attendance/mark", json=self.payload(self.driver)).status_code, 201)
        corrected = self.client.post("/attendance/mark", json=self.payload(self.driver, "Leave"))
        self.assertEqual(corrected.status_code, 201); self.assertEqual(corrected.json()["status"], "Leave")
        self.assertEqual(len(self.client.get(f"/attendance/driver/{self.driver.driver_id}/history").json()), 1)
        self.set_role(self.manager)
        self.assertEqual(self.client.post("/attendance/mark", json=self.payload(self.other_driver, "Absent")).status_code, 201)

    def test_dispatcher_is_read_only_and_driver_is_own_history_only(self):
        self.client.post("/attendance/mark", json=self.payload(self.driver, day="2026-08-28"))
        self.client.post("/attendance/mark", json=self.payload(self.other_driver, day="2026-08-29"))
        self.set_role(self.dispatcher)
        self.assertEqual(len(self.client.get("/attendance/fleet?start_date=2026-08-28&end_date=2026-08-29").json()), 2)
        self.assertEqual(self.client.post("/attendance/mark", json=self.payload(self.driver)).status_code, 403)
        self.set_role(self.driver_user)
        self.assertEqual(len(self.client.get("/attendance/me/history").json()), 1)
        self.assertEqual(self.client.get(f"/attendance/driver/{self.other_driver.driver_id}/history").status_code, 403)
        self.assertEqual(self.client.post("/attendance/mark", json=self.payload(self.driver)).status_code, 403)

    def test_daily_attendance_feeds_driver_analytics(self):
        self.client.post("/attendance/mark", json=self.payload(self.driver, "Present"))
        self.client.post("/attendance/mark", json=self.payload(self.driver, "Leave", "2026-08-29"))
        analytics = self.client.get("/analytics/driver-performance")
        self.assertEqual(analytics.status_code, 200)
        item = next(row for row in analytics.json()["drivers"] if row["driver_id"] == str(self.driver.driver_id))
        self.assertEqual(item["attendance_records"], 2); self.assertEqual(item["attendance_check_ins"], 1); self.assertEqual(item["attendance_rate"], 50.0)


if __name__ == "__main__":
    unittest.main()
