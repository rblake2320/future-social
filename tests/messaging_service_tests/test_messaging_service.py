import unittest
import json
from src.messaging_service.app import create_messaging_app # Adjusted import
from src.messaging_service.models import db, ConversationModel, MessageModel # Adjusted import

class MessagingServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_messaging_app(database_uri="sqlite:///:memory:")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.user1_id = 1
        self.user2_id = 2
        self.user3_id = 3

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_conversation(self, participant_ids):
        return self.client.post(
            "/conversations",
            data=json.dumps({"participant_ids": participant_ids}),
            content_type="application/json"
        )

    def _send_message(self, conversation_id, sender_id, text_content):
        return self.client.post(
            f"/conversations/{conversation_id}/messages",
            data=json.dumps({"sender_id": sender_id, "text_content": text_content}),
            content_type="application/json"
        )

    def test_create_new_conversation_success(self):
        response = self._create_conversation([self.user1_id, self.user2_id])
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.get_data(as_text=True))
        self.assertIn("id", data)
        self.assertEqual(sorted(data["participant_ids"]), sorted([self.user1_id, self.user2_id]))
        # Verify it's in the DB
        self.assertIsNotNone(ConversationModel.find_by_id(data["id"]))

    def test_get_existing_conversation_success(self):
        # Create one first
        create_response = self._create_conversation([self.user1_id, self.user2_id])
        created_data = json.loads(create_response.get_data(as_text=True))
        
        # Attempt to create/get again with same participants
        get_response = self._create_conversation([self.user2_id, self.user1_id]) # Order shouldn't matter for 2 users
        self.assertEqual(get_response.status_code, 200)
        get_data = json.loads(get_response.get_data(as_text=True))
        self.assertEqual(get_data["id"], created_data["id"])

    def test_create_conversation_invalid_participants(self):
        response = self._create_conversation([self.user1_id]) # Less than 2 participants
        self.assertEqual(response.status_code, 400)
        self.assertIn("Valid participant_ids list (at least 2) is required", response.get_data(as_text=True))

    def test_send_message_success(self):
        conv_response = self._create_conversation([self.user1_id, self.user2_id])
        conv_id = json.loads(conv_response.get_data(as_text=True))["id"]

        msg_response = self._send_message(conv_id, self.user1_id, "Hello User 2!")
        self.assertEqual(msg_response.status_code, 201)
        msg_data = json.loads(msg_response.get_data(as_text=True))
        self.assertEqual(msg_data["conversation_id"], conv_id)
        self.assertEqual(msg_data["sender_id"], self.user1_id)
        self.assertEqual(msg_data["text_content"], "Hello User 2!")
        # Verify message is in DB
        self.assertIsNotNone(MessageModel.find_by_id(msg_data["id"]))
        # Verify conversation last_message_at is updated
        conv = ConversationModel.find_by_id(conv_id)
        msg = MessageModel.find_by_id(msg_data["id"])
        self.assertEqual(conv.last_message_at, msg.created_at)

    def test_send_message_conversation_not_found(self):
        response = self._send_message(999, self.user1_id, "Test")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Conversation not found", response.get_data(as_text=True))

    def test_send_message_sender_not_in_conversation(self):
        conv_response = self._create_conversation([self.user1_id, self.user2_id])
        conv_id = json.loads(conv_response.get_data(as_text=True))["id"]

        msg_response = self._send_message(conv_id, self.user3_id, "Intruder message") # user3 is not in conv
        self.assertEqual(msg_response.status_code, 403)
        self.assertIn("Sender not part of this conversation", msg_response.get_data(as_text=True))

    def test_send_message_missing_fields(self):
        conv_response = self._create_conversation([self.user1_id, self.user2_id])
        conv_id = json.loads(conv_response.get_data(as_text=True))["id"]
        response = self.client.post(
            f"/conversations/{conv_id}/messages",
            data=json.dumps({"sender_id": self.user1_id}), # Missing text_content
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Sender ID and text content are required", response.get_data(as_text=True))

    def test_get_messages_success(self):
        conv_response = self._create_conversation([self.user1_id, self.user2_id])
        conv_id = json.loads(conv_response.get_data(as_text=True))["id"]

        self._send_message(conv_id, self.user1_id, "Message 1")
        import time; time.sleep(0.01) # Ensure order
        self._send_message(conv_id, self.user2_id, "Message 2")

        get_msg_response = self.client.get(f"/conversations/{conv_id}/messages")
        self.assertEqual(get_msg_response.status_code, 200)
        messages = json.loads(get_msg_response.get_data(as_text=True))
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["text_content"], "Message 1") # Ordered by asc created_at
        self.assertEqual(messages[1]["text_content"], "Message 2")

    def test_get_messages_conversation_not_found(self):
        response = self.client.get("/conversations/999/messages")
        self.assertEqual(response.status_code, 404)

    def test_get_user_conversations_list_success(self):
        # Conv 1: user1 and user2
        conv1_response = self._create_conversation([self.user1_id, self.user2_id])
        conv1_id = json.loads(conv1_response.get_data(as_text=True))["id"]
        self._send_message(conv1_id, self.user1_id, "Hi user2 from user1")
        import time; time.sleep(0.01)

        # Conv 2: user1 and user3
        conv2_response = self._create_conversation([self.user1_id, self.user3_id])
        conv2_id = json.loads(conv2_response.get_data(as_text=True))["id"]
        self._send_message(conv2_id, self.user3_id, "Hi user1 from user3")
        import time; time.sleep(0.01)

        # Conv 3: user2 and user3 (user1 not involved)
        conv3_response = self._create_conversation([self.user2_id, self.user3_id])
        conv3_id = json.loads(conv3_response.get_data(as_text=True))["id"]
        self._send_message(conv3_id, self.user2_id, "Hi user3 from user2")

        # Get conversations for user1
        response = self.client.get(f"/users/{self.user1_id}/conversations")
        self.assertEqual(response.status_code, 200)
        user1_convs = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(user1_convs), 2)
        # Check if ordered by last_message_at desc (conv2 should be first as its message was later)
        self.assertEqual(user1_convs[0]["id"], conv2_id)
        self.assertEqual(user1_convs[1]["id"], conv1_id)

        # Get conversations for user2
        response_user2 = self.client.get(f"/users/{self.user2_id}/conversations")
        self.assertEqual(response_user2.status_code, 200)
        user2_convs = json.loads(response_user2.get_data(as_text=True))
        self.assertEqual(len(user2_convs), 2)
        # Conv3 should be first for user2
        self.assertEqual(user2_convs[0]["id"], conv3_id)
        self.assertEqual(user2_convs[1]["id"], conv1_id)

if __name__ == "__main__":
    unittest.main()

