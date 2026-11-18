import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from auth_utils import current_user_from_jwt
from extensions import db
from models import CheckIn

trips_bp = Blueprint("trips_bp", __name__, url_prefix="/api/trips")

@trips_bp.post("/checkin")
@jwt_required()
def check_in():
    user = current_user_from_jwt()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    activity_id = request.form.get("activity_id")
    notes = request.form.get("notes", "")

    if not activity_id:
        return jsonify({"error": "Activity ID is required"}), 400

    photo_url = None
    
    # Handle the image file upload
    if 'photo' in request.files:
        file = request.files['photo']
        if file.filename != '':
            # Create a safe, unique filename using the user ID and timestamp
            filename = secure_filename(f"{user.id}_{int(datetime.now().timestamp())}_{file.filename}")
            upload_folder = os.path.join(current_app.root_path, 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            photo_url = f"/uploads/{filename}"

    # Save the check-in to the database
    new_checkin = CheckIn(
        user_id=user.id,
        activity_id=activity_id,
        photo_url=photo_url,
        notes=notes
    )
    db.session.add(new_checkin)
    db.session.commit()

    return jsonify({"message": "Check-in saved successfully!", "photo_url": photo_url}), 201