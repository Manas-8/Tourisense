import re
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from models import User


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def json_error(message, status_code):
    return jsonify(status="error", error=message), status_code


def normalize_email(email):
    return email.strip().lower()


def is_valid_email(email):
    return bool(EMAIL_RE.match(email or ""))


def is_strong_password(password):
    return (
        isinstance(password, str)
        and len(password) >= 8
        and any(char.isalpha() for char in password)
        and any(char.isdigit() for char in password)
    )


def safe_user(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }


def current_user_from_jwt():
    user_id = get_jwt_identity()
    if user_id is None:
        return None
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return None
    return User.query.get(user_id)


def require_roles(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            verify_jwt_in_request()
            user = current_user_from_jwt()
            if user is None or not user.active:
                return json_error("User account is inactive.", 403)
            if roles and user.role not in roles:
                return json_error("You are not authorized to access this resource.", 403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def get_request_claims():
    return get_jwt()
