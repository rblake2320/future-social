import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from .models import db, PostModel # Assuming models.py is in the same directory

def create_post_app(database_uri=None):
    app = Flask(__name__)

    if database_uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
            "DATABASE_URL", "postgresql://user:password@localhost:5432/fs_db"
        ) # Ensure this matches your actual DB setup or use a default for dev
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # --- Post CRUD Endpoints ---
    @app.route("/posts", methods=["POST"])
    def create_post():
        data = request.get_json()
        user_id = data.get("user_id") # In a real system, this would come from auth token
        text_content = data.get("text_content")
        media_urls = data.get("media_urls")
        content_type = data.get("content_type", "text")

        if not user_id:
            return jsonify({"message": "User ID is required"}), 400
        if not text_content and not media_urls:
            return jsonify({"message": "Post cannot be empty"}), 400

        new_post = PostModel(
            user_id=user_id, 
            text_content=text_content, 
            media_urls=media_urls, 
            content_type=content_type
        )
        try:
            new_post.save_to_db()
            return jsonify(new_post.to_json()), 201
        except Exception as e:
            # Log e
            return jsonify({"message": "Something went wrong creating post"}), 500

    @app.route("/posts/<int:post_id>", methods=["GET"])
    def get_post(post_id):
        post = PostModel.find_by_id(post_id)
        if post:
            return jsonify(post.to_json()), 200
        return jsonify({"message": "Post not found"}), 404

    @app.route("/posts/<int:post_id>", methods=["PUT"])
    def update_post(post_id):
        data = request.get_json()
        post = PostModel.find_by_id(post_id)
        if not post:
            return jsonify({"message": "Post not found"}), 404

        # For MVP, assume only owner can update - in real app, check user_id from auth token matches post.user_id
        # current_user_id = get_jwt_identity() # Placeholder for getting user from token
        # if post.user_id != current_user_id:
        #     return jsonify({"message": "Unauthorized to update this post"}), 403

        post.text_content = data.get("text_content", post.text_content)
        post.media_urls = data.get("media_urls", post.media_urls)
        post.content_type = data.get("content_type", post.content_type)
        
        try:
            post.save_to_db() # SQLAlchemy handles update on commit if object is tracked
            return jsonify(post.to_json()), 200
        except Exception as e:
            # Log e
            return jsonify({"message": "Something went wrong updating post"}), 500

    @app.route("/posts/<int:post_id>", methods=["DELETE"])
    def delete_post(post_id):
        post = PostModel.find_by_id(post_id)
        if not post:
            return jsonify({"message": "Post not found"}), 404

        # For MVP, assume only owner can delete - in real app, check user_id from auth token matches post.user_id
        # current_user_id = get_jwt_identity() # Placeholder
        # if post.user_id != current_user_id:
        #     return jsonify({"message": "Unauthorized to delete this post"}), 403

        try:
            post.delete_from_db()
            return jsonify({"message": "Post deleted successfully"}), 200
        except Exception as e:
            # Log e
            return jsonify({"message": "Something went wrong deleting post"}), 500

    @app.route("/users/<int:user_id>/posts", methods=["GET"])
    def get_posts_by_user(user_id):
        # Add pagination later if needed via request.args.get('limit') and request.args.get('offset')
        posts = PostModel.find_by_user_id(user_id)
        return jsonify([post.to_json() for post in posts]), 200

    @app.route("/feed", methods=["GET"])
    def get_feed():
        # Basic feed for now, will be replaced by a proper Feed Service
        # Add pagination later
        posts = PostModel.get_all_posts()
        return jsonify([post.to_json() for post in posts]), 200

    return app

if __name__ == "__main__":
    # This part is for running the app directly for development/testing
    # It won't be used when running with a proper WSGI server like Gunicorn
    app = create_post_app("sqlite:///:memory:") # Example for in-memory SQLite
    with app.app_context():
        db.create_all() # Create tables if they don't exist
    app.run(port=5002, debug=True) # Running on a different port

