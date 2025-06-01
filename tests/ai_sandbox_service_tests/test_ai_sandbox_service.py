import unittest
import json
from datetime import datetime
from src.ai_sandbox_service.app import create_ai_sandbox_app # Adjusted import
from src.ai_sandbox_service.models import db, LearningModuleModel, UserProgressModel # Adjusted import

class AISandboxServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_ai_sandbox_app(database_uri="sqlite:///:memory:")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.user1_id = 1
        self.user2_id = 2

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_module(self, title, description="Test module", content_type="text", content_url=None, duration=30, difficulty="beginner"):
        return self.client.post(
            "/ai_sandbox/modules",
            data=json.dumps({
                "title": title,
                "description": description,
                "content_type": content_type,
                "content_url": content_url,
                "estimated_duration_minutes": duration,
                "difficulty_level": difficulty
            }),
            content_type="application/json"
        )

    def _update_progress(self, user_id, module_id, status):
        return self.client.post(
            f"/ai_sandbox/users/{user_id}/progress/{module_id}",
            data=json.dumps({"status": status}),
            content_type="application/json"
        )

    def test_create_learning_module_success(self):
        response = self._create_module("Intro to AI")
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["title"], "Intro to AI")
        self.assertEqual(data["difficulty_level"], "beginner")
        self.assertTrue(LearningModuleModel.find_by_id(data["id"]))

    def test_create_learning_module_missing_title(self):
        response = self.client.post(
            "/ai_sandbox/modules",
            data=json.dumps({"description": "Module without title"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Module title is required", response.get_data(as_text=True))

    def test_get_learning_module_success(self):
        create_res = self._create_module("Module Alpha")
        module_id = json.loads(create_res.get_data(as_text=True))["id"]
        response = self.client.get(f"/ai_sandbox/modules/{module_id}")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["title"], "Module Alpha")

    def test_get_learning_module_not_found(self):
        response = self.client.get("/ai_sandbox/modules/999")
        self.assertEqual(response.status_code, 404)

    def test_get_all_learning_modules(self):
        self._create_module("Module One")
        self._create_module("Module Two")
        response = self.client.get("/ai_sandbox/modules")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(data), 2)

    def test_update_user_progress_new_entry_in_progress(self):
        module_res = self._create_module("Progress Module 1")
        module_id = json.loads(module_res.get_data(as_text=True))["id"]
        response = self._update_progress(self.user1_id, module_id, "in_progress")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["user_id"], self.user1_id)
        self.assertEqual(data["module_id"], module_id)
        self.assertEqual(data["status"], "in_progress")
        self.assertIsNotNone(data["started_at"])
        self.assertIsNone(data["completed_at"])
        self.assertTrue(UserProgressModel.find_by_user_and_module(self.user1_id, module_id))

    def test_update_user_progress_to_completed(self):
        module_res = self._create_module("Progress Module 2")
        module_id = json.loads(module_res.get_data(as_text=True))["id"]
        self._update_progress(self.user1_id, module_id, "in_progress") # Start it first
        response = self._update_progress(self.user1_id, module_id, "completed")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["status"], "completed")
        self.assertIsNotNone(data["started_at"])
        self.assertIsNotNone(data["completed_at"])

    def test_update_user_progress_invalid_status(self):
        module_res = self._create_module("Progress Module 3")
        module_id = json.loads(module_res.get_data(as_text=True))["id"]
        response = self._update_progress(self.user1_id, module_id, "on_hold") # Invalid status
        self.assertEqual(response.status_code, 400)
        self.assertIn("Valid status (not_started, in_progress, completed) is required", response.get_data(as_text=True))

    def test_update_user_progress_module_not_found(self):
        response = self._update_progress(self.user1_id, 999, "in_progress")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Module not found", response.get_data(as_text=True))

    def test_get_user_progress_for_module_existing(self):
        module_res = self._create_module("Progress Module 4")
        module_id = json.loads(module_res.get_data(as_text=True))["id"]
        self._update_progress(self.user1_id, module_id, "completed")
        response = self.client.get(f"/ai_sandbox/users/{self.user1_id}/progress/{module_id}")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["status"], "completed")

    def test_get_user_progress_for_module_not_started_default(self):
        module_res = self._create_module("Progress Module 5")
        module_id = json.loads(module_res.get_data(as_text=True))["id"]
        # No progress entry created yet for this user/module
        response = self.client.get(f"/ai_sandbox/users/{self.user1_id}/progress/{module_id}")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["status"], "not_started")
        self.assertEqual(data["module_id"], module_id)
        self.assertEqual(data["user_id"], self.user1_id)

    def test_get_user_progress_for_module_module_not_found(self):
        response = self.client.get(f"/ai_sandbox/users/{self.user1_id}/progress/999")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Module not found", response.get_data(as_text=True))

    def test_get_all_user_progress(self):
        module1_res = self._create_module("User Progress All M1")
        module1_id = json.loads(module1_res.get_data(as_text=True))["id"]
        module2_res = self._create_module("User Progress All M2")
        module2_id = json.loads(module2_res.get_data(as_text=True))["id"]
        self._create_module("User Progress All M3") # Module not started by user1

        self._update_progress(self.user1_id, module1_id, "completed")
        self._update_progress(self.user1_id, module2_id, "in_progress")
        # User2 progress, should not appear for user1
        self._update_progress(self.user2_id, module1_id, "in_progress") 

        response = self.client.get(f"/ai_sandbox/users/{self.user1_id}/progress")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(data), 2)
        statuses = {item["status"] for item in data}
        module_ids = {item["module_id"] for item in data}
        self.assertIn("completed", statuses)
        self.assertIn("in_progress", statuses)
        self.assertIn(module1_id, module_ids)
        self.assertIn(module2_id, module_ids)

    def test_sandbox_status_endpoint(self):
        response = self.client.get("/api/ai_sandbox/status")
        self.assertEqual(response.status_code, 200)
        self.assertIn("AI Sandbox Service is active", response.get_data(as_text=True))

if __name__ == "__main__":
    unittest.main()

