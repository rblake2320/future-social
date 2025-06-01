import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from .models import db, GroupModel, GroupMemberModel # Assuming models.py is in the same directory

def create_group_app(database_uri=None):
    app = Flask(__name__)

    if database_uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
            "DATABASE_URL", "postgresql://user:password@localhost:5432/fs_db"
        )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    @app.route("/groups", methods=["POST"])
    def create_group():
        data = request.get_json()
        name = data.get("name")
        creator_id = data.get("creator_id") # In real app, from auth token
        description = data.get("description")

        if not name or not creator_id:
            return jsonify({"message": "Group name and creator ID are required"}), 400
        
        if GroupModel.find_by_name(name):
            return jsonify({"message": "Group name already exists"}), 400

        new_group = GroupModel(name=name, creator_id=creator_id, description=description)
        try:
            new_group.save_to_db()
            # Automatically add creator as the first member (admin)
            creator_membership = GroupMemberModel(group_id=new_group.id, user_id=creator_id, role="admin")
            creator_membership.save_to_db() # This will also update member_count via model logic
            return jsonify(new_group.to_json()), 201
        except Exception as e:
            # Log e
            db.session.rollback()
            return jsonify({"message": "Something went wrong creating group"}), 500

    @app.route("/groups/<int:group_id>", methods=["GET"])
    def get_group(group_id):
        group = GroupModel.find_by_id(group_id)
        if group:
            return jsonify(group.to_json()), 200
        return jsonify({"message": "Group not found"}), 404

    @app.route("/groups", methods=["GET"])
    def get_all_groups():
        # Add pagination later
        groups = GroupModel.get_all_groups()
        return jsonify([group.to_json() for group in groups]), 200

    @app.route("/groups/<int:group_id>/join", methods=["POST"])
    def join_group(group_id):
        data = request.get_json()
        user_id = data.get("user_id") # In real app, from auth token

        if not user_id:
            return jsonify({"message": "User ID is required"}), 400

        group = GroupModel.find_by_id(group_id)
        if not group:
            return jsonify({"message": "Group not found"}), 404
        
        if GroupMemberModel.find_by_group_and_user(group_id, user_id):
            return jsonify({"message": "User already a member of this group"}), 400
        
        new_member = GroupMemberModel(group_id=group_id, user_id=user_id, role="member")
        try:
            new_member.save_to_db() # This updates member_count
            return jsonify(new_member.to_json()), 201
        except Exception as e:
            # Log e
            db.session.rollback()
            return jsonify({"message": "Something went wrong joining group"}), 500

    @app.route("/groups/<int:group_id>/leave", methods=["POST"])
    def leave_group(group_id):
        data = request.get_json()
        user_id = data.get("user_id") # In real app, from auth token

        if not user_id:
            return jsonify({"message": "User ID is required"}), 400

        membership = GroupMemberModel.find_by_group_and_user(group_id, user_id)
        if not membership:
            return jsonify({"message": "User is not a member of this group"}), 404
        
        group = GroupModel.find_by_id(group_id)
        if group and group.creator_id == user_id and group.member_count <= 1:
             # Or implement group deletion logic if creator leaves and is last member
            return jsonify({"message": "Creator cannot leave the group if they are the only member. Consider deleting the group instead."}), 403

        try:
            membership.delete_from_db() # This updates member_count
            return jsonify({"message": "Successfully left the group"}), 200
        except Exception as e:
            # Log e
            db.session.rollback()
            return jsonify({"message": "Something went wrong leaving group"}), 500

    @app.route("/groups/<int:group_id>/members", methods=["GET"])
    def get_group_members_list(group_id):
        # Add pagination later
        group = GroupModel.find_by_id(group_id)
        if not group:
            return jsonify({"message": "Group not found"}), 404
        members = GroupMemberModel.get_group_members(group_id)
        return jsonify([member.to_json() for member in members]), 200

    @app.route("/users/<int:user_id>/groups", methods=["GET"])
    def get_user_groups_list(user_id):
        # Add pagination later
        memberships = GroupMemberModel.get_user_groups(user_id)
        groups_data = []
        for membership in memberships:
            group = GroupModel.find_by_id(membership.group_id)
            if group:
                groups_data.append(group.to_json()) # Could also include role from membership
        return jsonify(groups_data), 200

    # Add endpoints for updating group details, managing member roles (admin, moderator) later
    # Add endpoints for posting within a group (might integrate with PostService or be specific here)

    return app

if __name__ == "__main__":
    app = create_group_app("sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    app.run(port=5004, debug=True) # Running on a different port

