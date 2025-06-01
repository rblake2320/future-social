import unittest
import json
from src.group_service.app import create_group_app # Adjusted import
from src.group_service.models import db, GroupModel, GroupMemberModel # Adjusted import

class GroupServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_group_app(database_uri="sqlite:///:memory:")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.user1_id = 1 # Creator
        self.user2_id = 2 # Member
        self.user3_id = 3 # Another member

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_group(self, name, creator_id, description="Test group description"):
        return self.client.post(
            "/groups",
            data=json.dumps({"name": name, "creator_id": creator_id, "description": description}),
            content_type="application/json"
        )

    def _join_group(self, group_id, user_id):
        return self.client.post(
            f"/groups/{group_id}/join",
            data=json.dumps({"user_id": user_id}),
            content_type="application/json"
        )

    def _leave_group(self, group_id, user_id):
        return self.client.post(
            f"/groups/{group_id}/leave",
            data=json.dumps({"user_id": user_id}),
            content_type="application/json"
        )

    def test_create_group_success(self):
        response = self._create_group("Test Group Alpha", self.user1_id)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["name"], "Test Group Alpha")
        self.assertEqual(data["creator_id"], self.user1_id)
        self.assertEqual(data["member_count"], 1) # Creator is automatically a member
        # Verify creator is admin
        membership = GroupMemberModel.find_by_group_and_user(data["id"], self.user1_id)
        self.assertIsNotNone(membership)
        self.assertEqual(membership.role, "admin")

    def test_create_group_duplicate_name(self):
        self._create_group("Test Group Beta", self.user1_id)
        response = self._create_group("Test Group Beta", self.user2_id)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Group name already exists", response.get_data(as_text=True))

    def test_create_group_missing_fields(self):
        response = self.client.post(
            "/groups",
            data=json.dumps({"name": "Missing Creator Group"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Group name and creator ID are required", response.get_data(as_text=True))

    def test_get_group_success(self):
        create_res = self._create_group("Fetchable Group", self.user1_id)
        group_id = json.loads(create_res.get_data(as_text=True))["id"]
        response = self.client.get(f"/groups/{group_id}")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["name"], "Fetchable Group")

    def test_get_group_not_found(self):
        response = self.client.get("/groups/999")
        self.assertEqual(response.status_code, 404)

    def test_get_all_groups(self):
        self._create_group("Group One", self.user1_id)
        self._create_group("Group Two", self.user2_id)
        response = self.client.get("/groups")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(data), 2)

    def test_join_group_success(self):
        create_res = self._create_group("Joinable Group", self.user1_id)
        group_id = json.loads(create_res.get_data(as_text=True))["id"]
        response = self._join_group(group_id, self.user2_id)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["user_id"], self.user2_id)
        self.assertEqual(data["group_id"], group_id)
        self.assertEqual(data["role"], "member")
        group = GroupModel.find_by_id(group_id)
        self.assertEqual(group.member_count, 2) # Creator + new member

    def test_join_group_already_member(self):
        create_res = self._create_group("Group Gamma", self.user1_id)
        group_id = json.loads(create_res.get_data(as_text=True))["id"]
        self._join_group(group_id, self.user2_id) # user2 joins
        response = self._join_group(group_id, self.user2_id) # user2 tries to join again
        self.assertEqual(response.status_code, 400)
        self.assertIn("User already a member of this group", response.get_data(as_text=True))

    def test_join_group_not_found(self):
        response = self._join_group(999, self.user1_id)
        self.assertEqual(response.status_code, 404)

    def test_leave_group_success(self):
        create_res = self._create_group("Leavable Group", self.user1_id)
        group_id = json.loads(create_res.get_data(as_text=True))["id"]
        self._join_group(group_id, self.user2_id) # user2 joins
        group = GroupModel.find_by_id(group_id)
        self.assertEqual(group.member_count, 2)

        response = self._leave_group(group_id, self.user2_id) # user2 leaves
        self.assertEqual(response.status_code, 200)
        self.assertIn("Successfully left the group", response.get_data(as_text=True))
        group = GroupModel.find_by_id(group_id)
        self.assertEqual(group.member_count, 1)
        self.assertIsNone(GroupMemberModel.find_by_group_and_user(group_id, self.user2_id))

    def test_leave_group_not_member(self):
        create_res = self._create_group("Group Delta", self.user1_id)
        group_id = json.loads(create_res.get_data(as_text=True))["id"]
        response = self._leave_group(group_id, self.user2_id) # user2 was never a member
        self.assertEqual(response.status_code, 404)
        self.assertIn("User is not a member of this group", response.get_data(as_text=True))

    def test_creator_leave_group_last_member(self):
        create_res = self._create_group("Solo Creator Group", self.user1_id)
        group_id = json.loads(create_res.get_data(as_text=True))["id"]
        response = self._leave_group(group_id, self.user1_id)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Creator cannot leave the group if they are the only member", response.get_data(as_text=True))

    def test_get_group_members_list(self):
        create_res = self._create_group("Popular Group", self.user1_id)
        group_id = json.loads(create_res.get_data(as_text=True))["id"]
        self._join_group(group_id, self.user2_id)
        self._join_group(group_id, self.user3_id)

        response = self.client.get(f"/groups/{group_id}/members")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(data), 3)
        user_ids_in_response = {member["user_id"] for member in data}
        self.assertEqual(user_ids_in_response, {self.user1_id, self.user2_id, self.user3_id})

    def test_get_user_groups_list(self):
        group1_res = self._create_group("User1 Group1", self.user1_id)
        group1_id = json.loads(group1_res.get_data(as_text=True))["id"]
        
        group2_res = self._create_group("User1 Group2", self.user1_id)
        group2_id = json.loads(group2_res.get_data(as_text=True))["id"]

        group3_res = self._create_group("User2 Group1", self.user2_id)
        # user1 also joins group3
        self._join_group(json.loads(group3_res.get_data(as_text=True))["id"], self.user1_id)

        response = self.client.get(f"/users/{self.user1_id}/groups")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(len(data), 3)
        group_names_in_response = {group["name"] for group in data}
        self.assertEqual(group_names_in_response, {"User1 Group1", "User1 Group2", "User2 Group1"})

if __name__ == "__main__":
    unittest.main()

