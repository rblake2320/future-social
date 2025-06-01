import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from .models import db, ConversationModel, MessageModel # Assuming models.py is in the same directory

def create_messaging_app(database_uri=None):
    app = Flask(__name__)

    if database_uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
            "DATABASE_URL", "postgresql://user:password@localhost:5432/fs_db"
        )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    @app.route("/conversations", methods=["POST"])
    def create_or_get_conversation():
        data = request.get_json()
        participant_ids = data.get("participant_ids")

        if not participant_ids or not isinstance(participant_ids, list) or len(participant_ids) < 2:
            return jsonify({"message": "Valid participant_ids list (at least 2) is required"}), 400
        
        # For 2-person chats, try to find existing one
        # The model __init__ sorts 2-person participant_ids for canonical representation
        # For group chats (future), this logic would be different
        existing_conversation = None
        if len(participant_ids) == 2:
            existing_conversation = ConversationModel.find_by_participants(participant_ids)
        
        if existing_conversation:
            return jsonify(existing_conversation.to_json()), 200

        new_conversation = ConversationModel(participant_ids=participant_ids)
        try:
            new_conversation.save_to_db()
            return jsonify(new_conversation.to_json()), 201
        except Exception as e:
            # Log e
            return jsonify({"message": "Something went wrong creating conversation"}), 500

    @app.route("/conversations/<int:conversation_id>/messages", methods=["POST"])
    def send_message(conversation_id):
        data = request.get_json()
        sender_id = data.get("sender_id") # In real app, from auth token
        text_content = data.get("text_content")

        if not sender_id or not text_content:
            return jsonify({"message": "Sender ID and text content are required"}), 400

        conversation = ConversationModel.find_by_id(conversation_id)
        if not conversation:
            return jsonify({"message": "Conversation not found"}), 404
        
        # Basic check if sender is part of the conversation
        if sender_id not in conversation.participant_ids:
            return jsonify({"message": "Sender not part of this conversation"}), 403

        new_message = MessageModel(conversation_id=conversation_id, sender_id=sender_id, text_content=text_content)
        try:
            new_message.save_to_db() # This also updates conversation.last_message_at
            return jsonify(new_message.to_json()), 201
        except Exception as e:
            # Log e
            return jsonify({"message": "Something went wrong sending message"}), 500

    @app.route("/conversations/<int:conversation_id>/messages", methods=["GET"])
    def get_messages(conversation_id):
        # Add pagination later via request.args
        conversation = ConversationModel.find_by_id(conversation_id)
        if not conversation:
            return jsonify({"message": "Conversation not found"}), 404
        
        # Basic check if requesting user is part of the conversation (would get user_id from auth token)
        # current_user_id = get_jwt_identity() # Placeholder
        # if current_user_id not in conversation.participant_ids:
        #     return jsonify({"message": "Unauthorized to view these messages"}), 403

        messages = MessageModel.get_conversation_messages(conversation_id)
        return jsonify([message.to_json() for message in messages]), 200

    @app.route("/users/<int:user_id>/conversations", methods=["GET"])
    def get_user_conversations_list(user_id):
        # Add pagination later
        conversations = ConversationModel.get_user_conversations(user_id)
        return jsonify([conv.to_json() for conv in conversations]), 200

    return app

if __name__ == "__main__":
    app = create_messaging_app("sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    app.run(port=5003, debug=True) # Running on a different port

