import unittest
import json
from datetime import datetime
from src.ai_sandbox_service.app import create_ai_sandbox_app
from src.ai_sandbox_service.models import db, LearningModuleModel, UserProgressModel, UserAIPreferenceModel
# Removed: from .test_ai_sandbox_service import AISandboxServiceTestCase - not needed if CombinedAISandboxTests is removed

class AISandboxServicePersonalizationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_ai_sandbox_app(database_uri="sqlite:///:memory:")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.user1_id = 1
        self.user2_id = 2

        # Pre-populate some modules for recommendation testing
        self.module1 = self._create_module_direct("Introduction to Python Programming", difficulty="beginner")
        self.module2 = self._create_module_direct("Machine Learning Basics", difficulty="intermediate")
        self.module3 = self._create_module_direct("Advanced Neural Networks", difficulty="advanced")
        self.module4 = self._create_module_direct("Natural Language Processing with Python", difficulty="intermediate")
        self.module5 = self._create_module_direct("Data Science Toolkit", difficulty="beginner")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_module_direct(self, title, description="Test module", content_type="text", content_url=None, duration=30, difficulty="beginner"):
        module = LearningModuleModel(title=title, description=description, content_type=content_type, content_url=content_url, estimated_duration_minutes=duration, difficulty_level=difficulty)
        module.save_to_db()
        return module

    def _update_progress_direct(self, user_id, module_id, status):
        progress = UserProgressModel.find_by_user_and_module(user_id, module_id)
        if not progress:
            progress = UserProgressModel(user_id=user_id, module_id=module_id)
        
        previous_status = progress.status
        progress.status = status
        if status == "in_progress":
            if not progress.started_at:
                progress.started_at = datetime.utcnow()
            progress.completed_at = None
        elif status == "completed":
            if not progress.started_at:
                progress.started_at = datetime.utcnow()
            progress.completed_at = datetime.utcnow()
            
            if previous_status != "completed": # Only update interests once on first completion
                user_prefs = UserAIPreferenceModel.get_or_create(user_id)
                module = LearningModuleModel.find_by_id(module_id)
                if module:
                    interest_tags = [word.lower() for word in module.title.split() if len(word) > 3]
                    if interest_tags:
                        user_prefs.update_interests(interest_tags) # This method now handles flag_modified and save
        elif status == "not_started":
            progress.started_at = None
            progress.completed_at = None
        progress.save_to_db()
        return progress

    def test_get_user_ai_preferences_new_user(self):
        response = self.client.get(f"/ai_sandbox/users/{self.user1_id}/preferences")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["user_id"], self.user1_id)
        self.assertEqual(data["inferred_interests"], [])
        self.assertTrue(UserAIPreferenceModel.find_by_user_id(self.user1_id))

    def test_update_user_ai_preferences_add_interests(self):
        response = self.client.put(
            f"/ai_sandbox/users/{self.user1_id}/preferences",
            data=json.dumps({"add_interests": ["python", "machine_learning"]}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertIn("python", data["inferred_interests"])
        self.assertIn("machine_learning", data["inferred_interests"])

    def test_update_user_ai_preferences_remove_interests(self):
        prefs = UserAIPreferenceModel.get_or_create(self.user1_id)
        prefs.update_interests(["python", "nlp", "deep_learning"]) # This now saves correctly
        
        response = self.client.put(
            f"/ai_sandbox/users/{self.user1_id}/preferences",
            data=json.dumps({"remove_interests": ["nlp"]}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertNotIn("nlp", data["inferred_interests"], f"Interests found: {data['inferred_interests']}")
        self.assertIn("python", data["inferred_interests"])

    def test_update_user_ai_preferences_no_valid_data(self):
        response = self.client.put(
            f"/ai_sandbox/users/{self.user1_id}/preferences",
            data=json.dumps({}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("No interests provided for update", response.get_data(as_text=True))

    def test_interest_update_on_module_completion(self):
        self._update_progress_direct(self.user1_id, self.module1.id, "completed")
        user_prefs = UserAIPreferenceModel.find_by_user_id(self.user1_id)
        self.assertIsNotNone(user_prefs)
        self.assertIn("introduction", user_prefs.inferred_interests)
        self.assertIn("python", user_prefs.inferred_interests)
        self.assertIn("programming", user_prefs.inferred_interests)

    def test_get_learning_recommendations_no_interests(self):
        response = self.client.get(f"/ai_sandbox/users/{self.user1_id}/recommendations")
        self.assertEqual(response.status_code, 200)
        recommendations = json.loads(response.get_data(as_text=True))
        self.assertTrue(len(recommendations) > 0, "Expected fallback recommendations for new user")
        self.assertTrue(len(recommendations) <= 3)
        for rec in recommendations:
            self.assertIsNotNone(LearningModuleModel.find_by_id(rec["id"])) 

    def test_get_learning_recommendations_with_interests(self):
        self._update_progress_direct(self.user1_id, self.module1.id, "completed")
        response = self.client.get(f"/ai_sandbox/users/{self.user1_id}/recommendations")
        self.assertEqual(response.status_code, 200)
        recommendations = json.loads(response.get_data(as_text=True))
        self.assertTrue(len(recommendations) > 0, "Expected recommendations based on interests")
        found_python_related_recommendation = any(rec["id"] == self.module4.id for rec in recommendations)
        self.assertTrue(found_python_related_recommendation, "Expected Python-related module (module4) recommendation")
        for rec in recommendations:
            self.assertNotEqual(rec["id"], self.module1.id)

    def test_get_learning_recommendations_filters_completed_modules(self):
        self._update_progress_direct(self.user1_id, self.module1.id, "completed")
        self._update_progress_direct(self.user1_id, self.module4.id, "completed")
        response = self.client.get(f"/ai_sandbox/users/{self.user1_id}/recommendations")
        self.assertEqual(response.status_code, 200)
        recommendations = json.loads(response.get_data(as_text=True))
        recommended_ids = {rec["id"] for rec in recommendations}
        self.assertNotIn(self.module1.id, recommended_ids)
        self.assertNotIn(self.module4.id, recommended_ids)
        self.assertTrue(len(recommendations) > 0, "Expected some recommendations even after filtering completed ones")

    def test_get_learning_recommendations_fallback_if_no_match(self):
        prefs = UserAIPreferenceModel.get_or_create(self.user1_id)
        prefs.update_interests(["quantum_computing_for_beginners"])
        response = self.client.get(f"/ai_sandbox/users/{self.user1_id}/recommendations")
        self.assertEqual(response.status_code, 200)
        recommendations = json.loads(response.get_data(as_text=True))
        self.assertTrue(len(recommendations) > 0, "Expected fallback recommendations when no direct match")
        self.assertTrue(len(recommendations) <= 3)

if __name__ == "__main__":
    unittest.main()

