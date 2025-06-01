from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# It's assumed that the db instance will be initialized in the app factory
# For now, we define it here. In a real multi-service setup with shared DB or separate DBs,
# this would be handled more carefully, possibly with a shared library or by passing the db instance.
# For this MVP stage, we'll assume each service might manage its own app and db context for its tables.
db = SQLAlchemy()

class PostModel(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False) # In a real microservice, this might be validated via User service API
    content_type = db.Column(db.String(50), nullable=False, default="text") # e.g., text, image, video, ai_project_share
    text_content = db.Column(db.Text, nullable=True)
    media_urls = db.Column(db.JSON, nullable=True) # List of URLs for images/videos
    # visibility = db.Column(db.String(50), default="public") # e.g., public, friends, private_group - for later
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, user_id, text_content=None, media_urls=None, content_type="text"):
        self.user_id = user_id
        self.text_content = text_content
        self.media_urls = media_urls
        self.content_type = content_type

    def to_json(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content_type": self.content_type,
            "text_content": self.text_content,
            "media_urls": self.media_urls,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, post_id):
        return cls.query.filter_by(id=post_id).first()

    @classmethod
    def find_by_user_id(cls, user_id, limit=10, offset=0):
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).limit(limit).offset(offset).all()

    @classmethod
    def get_all_posts(cls, limit=10, offset=0):
        # Basic feed for now, will be replaced by a proper Feed Service
        return cls.query.order_by(cls.created_at.desc()).limit(limit).offset(offset).all()

