from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Assuming db instance is initialized in the app factory
db = SQLAlchemy()

class LearningModuleModel(db.Model):
    __tablename__ = "learning_modules"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content_type = db.Column(db.String(50), nullable=False, default="text") # e.g., text, video, interactive_code_exercise
    content_url = db.Column(db.String(255), nullable=True) # URL to external content or path to internal
    estimated_duration_minutes = db.Column(db.Integer, nullable=True)
    difficulty_level = db.Column(db.String(50), default="beginner") # e.g., beginner, intermediate, advanced
    # category = db.Column(db.String(100), nullable=True) # e.g., "Introduction to ML", "Prompt Engineering"
    # prerequisites = db.Column(db.JSON, nullable=True) # List of module IDs that are prerequisites
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, title, description=None, content_type="text", content_url=None, estimated_duration_minutes=None, difficulty_level="beginner"):
        self.title = title
        self.description = description
        self.content_type = content_type
        self.content_url = content_url
        self.estimated_duration_minutes = estimated_duration_minutes
        self.difficulty_level = difficulty_level

    def to_json(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "content_type": self.content_type,
            "content_url": self.content_url,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "difficulty_level": self.difficulty_level,
            "created_at": self.created_at.isoformat()
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, module_id):
        return cls.query.filter_by(id=module_id).first()

    @classmethod
    def get_all_modules(cls, limit=50, offset=0):
        return cls.query.order_by(cls.id.asc()).limit(limit).offset(offset).all()

class UserProgressModel(db.Model):
    __tablename__ = "user_progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey("learning_modules.id"), nullable=False)
    status = db.Column(db.String(50), default="not_started") # e.g., not_started, in_progress, completed
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    # score = db.Column(db.Float, nullable=True) # For modules with quizzes/assessments
    # notes = db.Column(db.Text, nullable=True) # User's personal notes on the module

    module = db.relationship("LearningModuleModel", backref=db.backref("user_progress_entries", lazy="dynamic"))

    __table_args__ = (db.UniqueConstraint("user_id", "module_id", name="_user_module_uc"),)

    def __init__(self, user_id, module_id, status="not_started"):
        self.user_id = user_id
        self.module_id = module_id
        self.status = status
        if status == "in_progress" and not self.started_at:
            self.started_at = datetime.utcnow()
        elif status == "completed" and not self.completed_at:
            self.completed_at = datetime.utcnow()
            if not self.started_at: # If marked completed directly
                 self.started_at = self.completed_at

    def to_json(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "module_id": self.module_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "module_title": self.module.title if self.module else None # Include module title for convenience
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_user_and_module(cls, user_id, module_id):
        return cls.query.filter_by(user_id=user_id, module_id=module_id).first()

    @classmethod
    def get_user_progress_for_all_modules(cls, user_id, limit=100, offset=0):
        return cls.query.filter_by(user_id=user_id).order_by(cls.module_id.asc()).limit(limit).offset(offset).all()

# Future: AIPersonalizationPreferenceModel
# user_id, preference_key (e.g., "learning_style", "preferred_topics"), preference_value, last_updated





class UserAIPreferenceModel(db.Model):
    __tablename__ = "user_ai_preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True) # Each user has one preference profile
    # For MVP, store interests as a JSON list of keywords/tags derived from completed/interacted modules
    # Example: ["machine_learning_basics", "nlp_concepts", "image_generation"]
    inferred_interests = db.Column(db.JSON, nullable=True, default=list)
    # Explicit preferences could be added later, e.g., user explicitly states interest in "deep_learning"
    # explicit_preferences = db.Column(db.JSON, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, user_id, inferred_interests=None):
        self.user_id = user_id
        self.inferred_interests = inferred_interests if inferred_interests is not None else []

    def to_json(self):
        return {
            "user_id": self.user_id,
            "inferred_interests": self.inferred_interests,
            "last_updated": self.last_updated.isoformat()
        }

    def update_interests(self, new_interest_tags):
        """Adds new unique interest tags to the user's profile."""
        if not self.inferred_interests:
            self.inferred_interests = []
        for tag in new_interest_tags:
            if tag not in self.inferred_interests:
                self.inferred_interests.append(tag)
        self.last_updated = datetime.utcnow()
        self.save_to_db()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_user_id(cls, user_id):
        return cls.query.filter_by(user_id=user_id).first()

    @classmethod
    def get_or_create(cls, user_id):
        preference = cls.find_by_user_id(user_id)
        if not preference:
            preference = cls(user_id=user_id)
            preference.save_to_db()
        return preference

