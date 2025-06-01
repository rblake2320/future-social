import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from .models import db, UserModel

def create_app(database_uri=None):
    app = Flask(__name__)

    # Configure database
    if database_uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    else:
        # Default to environment variable or a local default for development
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
            "DATABASE_URL", "postgresql://user:password@localhost:5432/fs_db"
        )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    @app.route("/register", methods=["POST"])
    def register():
        data = request.get_json()
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username or not email or not password:
            return jsonify({"message": "Missing username, email, or password"}), 400

        if UserModel.find_by_username(username):
            return jsonify({"message": "Username already exists"}), 400
        
        if UserModel.find_by_email(email):
            return jsonify({"message": "Email already exists"}), 400

        new_user = UserModel(username=username, email=email, password=password)
        try:
            new_user.save_to_db()
            return jsonify({"message": "User created successfully"}), 201
        except Exception as e:
            # Log the exception e
            return jsonify({"message": "Something went wrong"}), 500

    @app.route("/login", methods=["POST"])
    def login():
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"message": "Missing username or password"}), 400

        user = UserModel.find_by_username(username)
        if not user:
            # Try finding by email as well for flexibility, though frontend should specify
            user = UserModel.find_by_email(username) 

        if user and UserModel.verify_hash(password, user.password_hash):
            # In a real app, generate and return a JWT token here
            return jsonify({"message": "Login successful", "user_id": user.id}), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401

    return app

if __name__ == "__main__":
    # This part is for running the app directly for development/testing
    # It won't be used when running with a proper WSGI server like Gunicorn
    # For local testing, you'd need to set up PostgreSQL or use SQLite for simplicity
    # For now, this is a placeholder as we'll test via Flask-Testing
    app = create_app("sqlite:///:memory:") # Example for in-memory SQLite for quick test
    with app.app_context():
        db.create_all() # Create tables if they don't exist
    app.run(debug=True)

