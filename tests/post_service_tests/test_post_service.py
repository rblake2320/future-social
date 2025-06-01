import unittest
import json
from datetime import datetime
from src.post_service.app import create_post_app # Adjusted import path
from src.post_service.models import db, PostModel # Adjusted import path

class PostServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_post_app(database_uri="sqlite:///:memory:")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.test_user_id = 1 # Assume a user ID for testing

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_post(self, user_id, text_content="Test post content", media_urls=None, content_type="text"):
        return self.client.post(
            "/posts",
            data=json.dumps({
                "user_id": user_id,
                "text_content": text_content,
                "media_urls": media_urls,
                "content_type": content_type
            }),
            content_type="application/json"
        )

    def test_create_text_post_success(self):
        response = self._create_post(self.test_user_id, "My first text post")
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["user_id"], self.test_user_id)
        self.assertEqual(data["text_content"], "My first text post")
        self.assertEqual(data["content_type"], "text")
        self.assertIsNone(data["media_urls"])
        self.assertTrue(PostModel.find_by_id(data["id"])) # Check if saved to DB

    def test_create_image_post_success(self):
        media = ["http://example.com/image.jpg"]
        response = self._create_post(self.test_user_id, "Check out this image!", media_urls=media, content_type="image")
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["content_type"], "image")
        self.assertEqual(data["media_urls"], media)

    def test_create_post_missing_user_id(self):
        response = self.client.post(
            "/posts",
            data=json.dumps({"text_content": "A post without user"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("User ID is required", response.get_data(as_text=True))

    def test_create_post_empty_content(self):
        response = self.client.post(
            "/posts",
            data=json.dumps({"user_id": self.test_user_id}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Post cannot be empty", response.get_data(as_text=True))

    def test_get_post_success(self):
        create_response = self._create_post(self.test_user_id, "Post to be fetched")
        post_id = json.loads(create_response.get_data(as_text=True))["id"]

        get_response = self.client.get(f"/posts/{post_id}")
        self.assertEqual(get_response.status_code, 200)
        data = json.loads(get_response.get_data(as_text=True))
        self.assertEqual(data["id"], post_id)
        self.assertEqual(data["text_content"], "Post to be fetched")

    def test_get_post_not_found(self):
        response = self.client.get("/posts/9999") # Non-existent post ID
        self.assertEqual(response.status_code, 404)
        self.assertIn("Post not found", response.get_data(as_text=True))

    def test_update_post_success(self):
        create_response = self._create_post(self.test_user_id, "Original content")
        post_id = json.loads(create_response.get_data(as_text=True))["id"]

        update_response = self.client.put(
            f"/posts/{post_id}",
            data=json.dumps({"text_content": "Updated content", "content_type": "edited_text"}),
            content_type="application/json"
        )
        self.assertEqual(update_response.status_code, 200)
        data = json.loads(update_response.get_data(as_text=True))
        self.assertEqual(data["text_content"], "Updated content")
        self.assertEqual(data["content_type"], "edited_text")

    def test_update_post_not_found(self):
        response = self.client.put(
            "/posts/9999",
            data=json.dumps({"text_content": "Updated content"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_post_success(self):
        create_response = self._create_post(self.test_user_id, "Post to be deleted")
        post_id = json.loads(create_response.get_data(as_text=True))["id"]

        delete_response = self.client.delete(f"/posts/{post_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertIn("Post deleted successfully", delete_response.get_data(as_text=True))
        self.assertIsNone(PostModel.find_by_id(post_id)) # Verify deleted from DB

    def test_delete_post_not_found(self):
        response = self.client.delete("/posts/9999")
        self.assertEqual(response.status_code, 404)

    def test_get_posts_by_user(self):
        self._create_post(self.test_user_id, "User 1 Post 1")
        self._create_post(self.test_user_id, "User 1 Post 2")
        self._create_post(self.test_user_id + 1, "User 2 Post 1") # Another user's post

        response = self.client.get(f"/users/{self.test_user_id}/posts")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["text_content"], "User 1 Post 2") # Ordered by desc created_at
        self.assertEqual(data[1]["text_content"], "User 1 Post 1")

    def test_get_feed_basic(self):
        self._create_post(self.test_user_id, "Feed Post 1")
        # Simulate time passing for ordering
        # In a real test, you might mock datetime or create posts with explicit different timestamps
        import time; time.sleep(0.01) 
        self._create_post(self.test_user_id + 1, "Feed Post 2")

        response = self.client.get("/feed")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(data), 2)
        # Assuming Feed Post 2 was created after Feed Post 1 due to sleep
        self.assertEqual(data[0]["text_content"], "Feed Post 2") 
        self.assertEqual(data[1]["text_content"], "Feed Post 1")

if __name__ == "__main__":
    unittest.main()

