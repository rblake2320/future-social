from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Assuming db instance is initialized in the app factory
db = SQLAlchemy()

class ConversationModel(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    # In a real microservice setup, participants might be stored more flexibly
    # or this service might call User service to validate user IDs.
    # For simplicity, storing as a JSON list of user IDs.
    participant_ids = db.Column(db.JSON, nullable=False) # e.g., [1, 2]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # type = db.Column(db.String(50), default="direct") # For future: direct, group_chat

    def __init__(self, participant_ids):
        # Ensure participant_ids are sorted to create a canonical representation for 2-person chats
        # This helps in finding existing conversations between two users easily.
        # For group chats (future), this might need adjustment.
        if len(participant_ids) == 2:
            self.participant_ids = sorted(list(set(participant_ids))) # Ensure unique and sorted
        else:
            self.participant_ids = list(set(participant_ids)) # For group chats, order might not matter or be handled differently

    def to_json(self):
        return {
            "id": self.id,
            "participant_ids": self.participant_ids,
            "created_at": self.created_at.isoformat(),
            "last_message_at": self.last_message_at.isoformat()
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, conversation_id):
        return cls.query.filter_by(id=conversation_id).first()

    @classmethod
    def find_by_participants(cls, participant_ids):
        # For 2-person chats, ensure we find regardless of order in input
        if len(participant_ids) == 2:
            sorted_participants = sorted(list(set(participant_ids)))
            # This query is a bit simplistic for JSON. A more robust way might involve checking array containment
            # or having a separate participants link table. For MVP, we query based on the sorted list.
            # This assumes participant_ids in DB is also stored sorted for 2-person chats.
            return cls.query.filter(cls.participant_ids == sorted_participants).first()
        # For group chats, a more complex query or different model structure might be needed.
        return None # Placeholder for group chat lookup

    @classmethod
    def get_user_conversations(cls, user_id, limit=20, offset=0):
        # This query checks if the user_id is present in the participant_ids JSON array.
        # This is not highly performant for large datasets with JSON. 
        # A linking table (UserConversations) would be better for scalability.
        return cls.query.filter(cls.participant_ids.contains(user_id)).order_by(cls.last_message_at.desc()).limit(limit).offset(offset).all()

class MessageModel(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False)
    sender_id = db.Column(db.Integer, nullable=False) # User ID of the sender
    text_content = db.Column(db.Text, nullable=False)
    # media_url = db.Column(db.String(255), nullable=True) # For future media messages
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # read_status = db.Column(db.JSON, nullable=True) # e.g., {"user_id_1": true, "user_id_2": false}

    conversation = db.relationship("ConversationModel", backref=db.backref("messages", lazy="dynamic"))

    def __init__(self, conversation_id, sender_id, text_content):
        self.conversation_id = conversation_id
        self.sender_id = sender_id
        self.text_content = text_content

    def to_json(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "sender_id": self.sender_id,
            "text_content": self.text_content,
            "created_at": self.created_at.isoformat()
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
        # Update conversation's last_message_at timestamp
        if self.conversation:
            self.conversation.last_message_at = self.created_at
            self.conversation.save_to_db()

    @classmethod
    def find_by_id(cls, message_id):
        return cls.query.filter_by(id=message_id).first()

    @classmethod
    def get_conversation_messages(cls, conversation_id, limit=50, offset=0):
        return cls.query.filter_by(conversation_id=conversation_id).order_by(cls.created_at.asc()).limit(limit).offset(offset).all()

