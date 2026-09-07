"""Integration coverage for the Admin-only User Management API."""
import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.deps import get_current_user
from app.core.security import verify_password
from app.models.user import RoleEnum, User
from database import Base, get_db
from main import app


class UserManagementIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        cls.Session = sessionmaker(bind=cls.engine, autocommit=False, autoflush=False, expire_on_commit=False)
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.Session()
            try:
                yield db
            finally:
                db.close()

        def override_current_user():
            return cls.current_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_current_user
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.client.close()
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.admin = self.make_user("admin", RoleEnum.Admin)
        self.fleet_manager = self.make_user("fleet", RoleEnum.FleetManager)
        self.dispatcher = self.make_user("dispatch", RoleEnum.Dispatcher)
        self.driver = self.make_user("driver", RoleEnum.Driver)
        type(self).current_user = self.as_current_user(self.admin)

    def db(self):
        return self.Session()

    @staticmethod
    def as_current_user(user):
        return SimpleNamespace(user_id=user.user_id, role=user.role, email=user.email, is_active=True)

    def make_user(self, label, role):
        db = self.db()
        user = User(full_name=label.title(), email=f"{label}@users.example.com", password="existing-hash", phone="9000000000", role=role, email_verified=True, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        db.close()
        return user

    def payload(self, **overrides):
        payload = {"full_name": "New Driver", "email": "new.driver@users.example.com", "password": "SafePassword123!", "phone": "9876543210", "address": "Coimbatore", "role": "Driver"}
        payload.update(overrides)
        return payload

    def test_admin_can_list_create_and_update_without_sensitive_data(self):
        response = self.client.get("/users")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 4)
        self.assertNotIn("password", response.json()["items"][0])
        self.assertNotIn("password_hash", response.json()["items"][0])

        response = self.client.post("/users", json=self.payload())
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertNotIn("password", body)
        db = self.db()
        created = db.query(User).filter(User.email == self.payload()["email"]).one()
        self.assertTrue(verify_password("SafePassword123!", created.password))
        db.close()

        response = self.client.put(f"/users/{body['user_id']}", json={"full_name": "Updated Driver", "role": "Dispatcher"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "Dispatcher")

    def test_filters_duplicate_and_last_admin_protection(self):
        self.assertEqual(self.client.get("/users", params={"search": "dispatch", "role": "Dispatcher"}).json()["total"], 1)
        self.assertEqual(self.client.post("/users", json=self.payload(email=self.driver.email)).status_code, 409)
        self.assertEqual(self.client.post("/users", json=self.payload(email="bad@example.com", role="Owner")).status_code, 422)
        self.assertEqual(self.client.patch(f"/users/{self.driver.user_id}/status", json={"is_active": False}).status_code, 200)
        self.assertEqual(self.client.get("/users", params={"role": "Driver", "is_active": "false"}).json()["total"], 1)
        self.assertEqual(self.client.patch(f"/users/{self.admin.user_id}/status", json={"is_active": False}).status_code, 409)
        self.assertEqual(self.client.put(f"/users/{self.admin.user_id}", json={"role": "FleetManager"}).status_code, 409)

    def test_non_admin_roles_are_forbidden(self):
        for user in (self.fleet_manager, self.dispatcher, self.driver):
            type(self).current_user = self.as_current_user(user)
            self.assertEqual(self.client.get("/users").status_code, 403)

    def test_unauthenticated_request_is_rejected(self):
        override = app.dependency_overrides.pop(get_current_user)
        try:
            self.assertEqual(self.client.get("/users").status_code, 401)
        finally:
            app.dependency_overrides[get_current_user] = override


if __name__ == "__main__":
    unittest.main()
