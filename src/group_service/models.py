from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Assuming db instance is initialized in the app factory
db = SQLAlchemy()

class GroupModel(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    creator_id = db.Column(db.Integer, nullable=False) # User ID of the creator
    # type = db.Column(db.String(50), default="public") # e.g., public, private, secret - for later
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    member_count = db.Column(db.Integer, default=1) # Starts with creator as a member

    def __init__(self, name, creator_id, description=None):
        self.name = name
        self.creator_id = creator_id
        self.description = description

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "creator_id": self.creator_id,
            "created_at": self.created_at.isoformat(),
            "member_count": self.member_count
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
    
    def update_member_count(self):
        self.member_count = GroupMemberModel.query.filter_by(group_id=self.id).count()
        self.save_to_db()

    @classmethod
    def find_by_id(cls, group_id):
        return cls.query.filter_by(id=group_id).first()

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()
    
    @classmethod
    def get_all_groups(cls, limit=20, offset=0):
        return cls.query.order_by(cls.created_at.desc()).limit(limit).offset(offset).all()

class GroupMemberModel(db.Model):
    __tablename__ = "group_members"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    role = db.Column(db.String(50), default="member") # e.g., member, admin, moderator
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    group = db.relationship("GroupModel", backref=db.backref("members", lazy="dynamic"))
    # user = db.relationship("UserModel") # If UserModel is in the same service or accessible

    __table_args__ = (db.UniqueConstraint("group_id", "user_id", name="_group_user_uc"),)

    def __init__(self, group_id, user_id, role="member"):
        self.group_id = group_id
        self.user_id = user_id
        self.role = role

    def to_json(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "user_id": self.user_id,
            "role": self.role,
            "joined_at": self.joined_at.isoformat()
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
        # Update group member count
        if self.group:
            self.group.update_member_count()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
        # Update group member count
        if self.group:
            self.group.update_member_count()

    @classmethod
    def find_by_group_and_user(cls, group_id, user_id):
        return cls.query.filter_by(group_id=group_id, user_id=user_id).first()
    
    @classmethod
    def get_group_members(cls, group_id, limit=50, offset=0):
        return cls.query.filter_by(group_id=group_id).limit(limit).offset(offset).all()

    @classmethod
    def get_user_groups(cls, user_id, limit=20, offset=0):
        return cls.query.filter_by(user_id=user_id).order_by(cls.joined_at.desc()).limit(limit).offset(offset).all()

