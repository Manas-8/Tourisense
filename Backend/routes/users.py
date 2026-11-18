from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from auth_utils import (
    current_user_from_jwt,
    is_strong_password,
    is_valid_email,
    json_error,
    normalize_email,
    safe_user,
)
from extensions import db
from models import User


users_bp = Blueprint("users_bp", __name__, url_prefix="/api/users")


@users_bp.get("/me")
@jwt_required()
def me():
    user = current_user_from_jwt()
    if user is None:
        return json_error("User account is inactive.", 403)
    if not user.active:
        return json_error("User account is inactive.", 403)
    return jsonify(safe_user(user))


@users_bp.patch("/me")
@jwt_required()
def update_me():
    user = current_user_from_jwt()
    if user is None or not user.active:
        return json_error("User account is inactive.", 403)

    payload = request.get_json(silent=True) or {}
    disallowed_fields = {"id", "role", "password_hash", "active"}
    if any(field in payload for field in disallowed_fields):
        return json_error("One or more fields cannot be updated.", 400)

    if "name" in payload:
        name = (payload.get("name") or "").strip()
        if not name:
            return json_error("Name cannot be empty.", 400)
        user.name = name

    if "email" in payload:
        email = normalize_email(payload.get("email") or "")
        if not email or not is_valid_email(email):
            return json_error("A valid email address is required.", 400)
        if email == "admin@gmail.com" and user.role != "admin":
            return json_error(
                "This email address is reserved for the government administrator and cannot be used for a tourist account.",
                409,
            )
        existing_user = User.query.filter(User.email == email, User.id != user.id).first()
        if existing_user:
            return json_error("An account with that email already exists.", 409)
        user.email = email

    db.session.commit()
    return jsonify(safe_user(user)), 200
