import unittest
import json
from src.user_service.app import create_app
from src.user_service.models import db, UserModel

class UserServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(database_uri="sqlite:///:memory:")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_registration_success(self):
        response = self.client.post(
            "/register",
            data=json.dumps({"username": "testuser", "email": "test@example.com", "password": "password123"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("User created successfully", response.get_data(as_text=True))
        # Verify user is in db
        user = UserModel.find_by_username("testuser")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")

    def test_user_registration_missing_fields(self):
        response = self.client.post(
            "/register",
            data=json.dumps({"username": "testuser", "email": "test@example.com"}), # Missing password
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing username, email, or password", response.get_data(as_text=True))

    def test_user_registration_duplicate_username(self):
        # First registration
        self.client.post(
            "/register",
            data=json.dumps({"username": "testuser", "email": "test1@example.com", "password": "password123"}),
            content_type="application/json"
        )
        # Attempt to register with same username
        response = self.client.post(
            "/register",
            data=json.dumps({"username": "testuser", "email": "test2@example.com", "password": "password456"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Username already exists", response.get_data(as_text=True))

    def test_user_registration_duplicate_email(self):
        # First registration
        self.client.post(
            "/register",
            data=json.dumps({"username": "testuser1", "email": "test@example.com", "password": "password123"}),
            content_type="application/json"
        )
        # Attempt to register with same email
        response = self.client.post(
            "/register",
            data=json.dumps({"username": "testuser2", "email": "test@example.com", "password": "password456"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Email already exists", response.get_data(as_text=True))

    def test_user_login_success(self):
        # Register user first
        self.client.post(
            "/register",
            data=json.dumps({"username": "loginuser", "email": "login@example.com", "password": "securepassword"}),
            content_type="application/json"
        )
        # Attempt login
        response = self.client.post(
            "/login",
            data=json.dumps({"username": "loginuser", "password": "securepassword"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Login successful", response.get_data(as_text=True))
        user_data = json.loads(response.get_data(as_text=True))
        self.assertIn("user_id", user_data)

    def test_user_login_invalid_username(self):
        response = self.client.post(
            "/login",
            data=json.dumps({"username": "nonexistentuser", "password": "password123"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid credentials", response.get_data(as_text=True))

    def test_user_login_incorrect_password(self):
        # Register user first
        self.client.post(
            "/register",
            data=json.dumps({"username": "loginuser2", "email": "login2@example.com", "password": "correctpassword"}),
            content_type="application/json"
        )
        # Attempt login with wrong password
        response = self.client.post(
            "/login",
            data=json.dumps({"username": "loginuser2", "password": "wrongpassword"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid credentials", response.get_data(as_text=True))

    def test_user_login_missing_fields(self):
        response = self.client.post(
            "/login",
            data=json.dumps({"username": "loginuser3"}), # Missing password
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing username or password", response.get_data(as_text=True))

if __name__ == "__main__":
    unittest.main()

