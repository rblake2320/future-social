import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from .models import db, LearningModuleModel, UserProgressModel, UserAIPreferenceModel

def create_ai_sandbox_app(database_uri=None):
    app = Flask(__name__)

    if database_uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
            "DATABASE_URL", "postgresql://user:password@localhost:5432/fs_db"
        )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # --- Learning Module Endpoints (Admin/Content Management) ---
    @app.route("/ai_sandbox/modules", methods=["POST"])
    def create_learning_module():
        data = request.get_json()
        title = data.get("title")
        if not title:
            return jsonify({"message": "Module title is required"}), 400
        
        new_module = LearningModuleModel(
            title=title,
            description=data.get("description"),
            content_type=data.get("content_type", "text"),
            content_url=data.get("content_url"),
            estimated_duration_minutes=data.get("estimated_duration_minutes"),
            difficulty_level=data.get("difficulty_level", "beginner")
        )
        try:
            new_module.save_to_db()
            return jsonify(new_module.to_json()), 201
        except Exception as e:
            app.logger.error(f"Error creating module: {e}")
            return jsonify({"message": "Something went wrong creating module"}), 500

    @app.route("/ai_sandbox/modules/<int:module_id>", methods=["GET"])
    def get_learning_module(module_id):
        module = LearningModuleModel.find_by_id(module_id)
        if module:
            return jsonify(module.to_json()), 200
        return jsonify({"message": "Module not found"}), 404

    @app.route("/ai_sandbox/modules", methods=["GET"])
    def get_all_learning_modules():
        modules = LearningModuleModel.get_all_modules()
        return jsonify([module.to_json() for module in modules]), 200

    # --- User Progress Endpoints ---
    @app.route("/ai_sandbox/users/<int:user_id>/progress/<int:module_id>", methods=["POST", "PUT"])
    def update_user_progress(user_id, module_id):
        data = request.get_json()
        status = data.get("status")

        if not status or status not in ["not_started", "in_progress", "completed"]:
            return jsonify({"message": "Valid status (not_started, in_progress, completed) is required"}), 400

        module = LearningModuleModel.find_by_id(module_id)
        if not module:
            return jsonify({"message": "Module not found"}), 404

        progress = UserProgressModel.find_by_user_and_module(user_id, module_id)
        if not progress:
            progress = UserProgressModel(user_id=user_id, module_id=module_id)
        
        previous_status = progress.status
        progress.status = status
        if status == "in_progress":
            if not progress.started_at:
                progress.started_at = datetime.utcnow()
            progress.completed_at = None
        elif status == "completed":
            if not progress.started_at:
                progress.started_at = datetime.utcnow()
            progress.completed_at = datetime.utcnow()
            if previous_status != "completed":
                try:
                    user_prefs = UserAIPreferenceModel.get_or_create(user_id)
                    interest_tags = [word.lower() for word in module.title.split() if len(word) > 3]
                    if interest_tags:
                        user_prefs.update_interests(interest_tags)
                except Exception as e:
                    app.logger.error(f"Error updating user preferences for user {user_id}: {e}")
        elif status == "not_started":
            progress.started_at = None
            progress.completed_at = None
            
        try:
            progress.save_to_db()
            return jsonify(progress.to_json()), 200
        except Exception as e:
            app.logger.error(f"Error updating progress for user {user_id}, module {module_id}: {e}")
            return jsonify({"message": "Something went wrong updating progress"}), 500

    @app.route("/ai_sandbox/users/<int:user_id>/progress/<int:module_id>", methods=["GET"])
    def get_user_progress_for_module(user_id, module_id):
        progress = UserProgressModel.find_by_user_and_module(user_id, module_id)
        if progress:
            return jsonify(progress.to_json()), 200
        module = LearningModuleModel.find_by_id(module_id)
        if not module:
            return jsonify({"message": "Module not found"}), 404
        default_progress = {
            "user_id": user_id,
            "module_id": module_id,
            "status": "not_started",
            "started_at": None,
            "completed_at": None,
            "module_title": module.title
        }
        return jsonify(default_progress), 200

    @app.route("/ai_sandbox/users/<int:user_id>/progress", methods=["GET"])
    def get_all_user_progress(user_id):
        progress_entries = UserProgressModel.get_user_progress_for_all_modules(user_id)
        return jsonify([p.to_json() for p in progress_entries]), 200

    # --- User AI Preferences & Recommendations Endpoints ---
    @app.route("/ai_sandbox/users/<int:user_id>/preferences", methods=["GET"])
    def get_user_ai_preferences(user_id):
        user_prefs = UserAIPreferenceModel.get_or_create(user_id)
        return jsonify(user_prefs.to_json()), 200

    @app.route("/ai_sandbox/users/<int:user_id>/preferences", methods=["PUT"])
    def update_user_ai_preferences(user_id):
        data = request.get_json()
        interests_to_add = data.get("add_interests", [])
        interests_to_remove = data.get("remove_interests", [])

        if not isinstance(interests_to_add, list) or not isinstance(interests_to_remove, list):
            return jsonify({"message": "Interests must be lists."}), 400

        user_prefs = UserAIPreferenceModel.get_or_create(user_id)
        
        # Ensure inferred_interests is a list to start with
        if user_prefs.inferred_interests is None:
            user_prefs.inferred_interests = []
            
        current_interests_set = set(user_prefs.inferred_interests)
        original_interests_set = set(user_prefs.inferred_interests) # For checking if changes were made
        
        for interest in interests_to_add:
            if isinstance(interest, str):
                current_interests_set.add(interest)
        
        for interest in interests_to_remove:
            if isinstance(interest, str):
                current_interests_set.discard(interest)
        
        new_interests_list = sorted(list(current_interests_set))

        if original_interests_set != current_interests_set:
            user_prefs.inferred_interests = new_interests_list
            user_prefs.last_updated = datetime.utcnow()
            try:
                user_prefs.save_to_db()
                return jsonify(user_prefs.to_json()), 200
            except Exception as e:
                app.logger.error(f"Error saving user preferences for user {user_id}: {e}")
                return jsonify({"message": "Something went wrong updating preferences"}), 500
        else:
            if not interests_to_add and not interests_to_remove and not data:
                 return jsonify({"message": "No interests provided for update"}), 400
            return jsonify(user_prefs.to_json()), 200

    @app.route("/ai_sandbox/users/<int:user_id>/recommendations", methods=["GET"])
    def get_learning_recommendations(user_id):
        user_prefs = UserAIPreferenceModel.get_or_create(user_id)
        user_interests = user_prefs.inferred_interests if user_prefs.inferred_interests else []

        user_progress_all = UserProgressModel.get_user_progress_for_all_modules(user_id)
        completed_or_started_module_ids = {p.module_id for p in user_progress_all if p.status in ["in_progress", "completed"]}

        recommendations = []
        if user_interests:
            all_modules_for_interest_match = LearningModuleModel.get_all_modules(limit=200) 
            for module in all_modules_for_interest_match:
                if module.id in completed_or_started_module_ids:
                    continue
                module_tags = [word.lower() for word in module.title.split() if len(word) > 3]
                if any(interest_tag in module_tags for interest_tag in user_interests):
                    recommendations.append(module.to_json())
                if len(recommendations) >= 5:
                    break
        
        if not recommendations: # Fallback if no interest-based recommendations or no interests initially
            fallback_modules_query = LearningModuleModel.get_all_modules(limit=10) # Get a slightly larger pool for fallback
            fallback_recommendations = []
            for module in fallback_modules_query:
                if module.id not in completed_or_started_module_ids:
                    fallback_recommendations.append(module.to_json())
                if len(fallback_recommendations) >= 3:
                    break
            return jsonify(fallback_recommendations), 200

        return jsonify(recommendations), 200

    @app.route("/api/ai_sandbox/status", methods=["GET"])
    def sandbox_status():
        return jsonify({"message": "AI Sandbox Service is active. Learning modules, progress tracking, and personalization available."}), 200

    return app

if __name__ == "__main__":
    app = create_ai_sandbox_app("sqlite:///:memory:")
    with app.app_context():
        db.create_all()
    app.run(port=5001, debug=True)

