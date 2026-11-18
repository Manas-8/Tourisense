from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

from auth_utils import (
    json_error,
    is_strong_password,
    is_valid_email,
    normalize_email,
    safe_user,
)
from extensions import db
from models import User


auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/auth")
RESERVED_PUBLIC_EMAILS = {"admin@gmail.com"}


def _parse_payload():
    return request.get_json(silent=True) or {}


@auth_bp.post("/register")
def register():
    payload = _parse_payload()

    name = (payload.get("name") or "").strip()
    email = normalize_email(payload.get("email") or "")
    password = payload.get("password") or ""

    if not name:
        return json_error("Name is required.", 400)
    if not email or not is_valid_email(email):
        return json_error("A valid email address is required.", 400)
    if email in RESERVED_PUBLIC_EMAILS:
        return json_error(
            "This email address is reserved for the government administrator and cannot be used for public registration.",
            409,
        )
    if not is_strong_password(password):
        return json_error(
            "Password must be at least 8 characters and include letters and numbers.",
            400,
        )

    if User.query.filter_by(email=email).first():
        return json_error("An account with that email already exists.", 409)

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role="tourist",
        active=True,
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(token=token, user=safe_user(user)), 201


@auth_bp.post("/login")
def login():
    payload = _parse_payload()

    email = normalize_email(payload.get("email") or "")
    password = payload.get("password") or ""

    if not email or not password:
        return json_error("Email and password are required.", 400)
    if not is_valid_email(email):
        return json_error("Invalid credentials.", 401)

    user = User.query.filter_by(email=email).first()
    if user is None or not check_password_hash(user.password_hash, password):
        return json_error("Invalid credentials.", 401)
    if not user.active:
        return json_error("User account is inactive.", 403)

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(token=token, user=safe_user(user)), 200
