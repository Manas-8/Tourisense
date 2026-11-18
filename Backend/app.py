import os

import click
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash
from flask_apscheduler import APScheduler

from routes.auth import auth_bp
from routes.users import users_bp
from routes.trips import trips_bp
from routes.ml import ml_bp
from routes.catalog import catalog_bp
from config import Config
from extensions import db, jwt, migrate
from models import User

import models  # noqa: F401


def create_app(config_class=Config):
    """Create and configure the Tourisense Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
    )
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    @jwt.unauthorized_loader
    def unauthorized_callback(message):
        return jsonify(status="error", error=message), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(message):
        return jsonify(status="error", error="Invalid authentication token."), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify(status="error", error="Authentication token has expired."), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify(status="error", error="Authentication token is no longer valid."), 401

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(trips_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(catalog_bp)

    # Keep the scheduler hook visible, but don't imply it is a data refresh pipeline.
    scheduler = APScheduler()
    scheduler.init_app(app)

    @scheduler.task('interval', id='scrape_data', minutes=3)
    def real_time_algorithm():
        with app.app_context():
            app.logger.info("Real-time refresh is not configured; source datasets remain unchanged.")
            
    if not app.config.get("TESTING"):
        scheduler.start()

    @app.cli.command("seed-admin")
    def seed_admin():
        """Create the development administrator from environment variables."""
        email = (os.environ.get("ADMIN_EMAIL") or "").strip().lower()
        password = os.environ.get("ADMIN_PASSWORD") or ""
        name = (os.environ.get("ADMIN_NAME") or "Government Administrator").strip()

        if not email or not password:
            raise click.UsageError(
                "ADMIN_EMAIL and ADMIN_PASSWORD must be configured before running seed-admin."
            )
        if User.query.filter_by(email=email).first():
            raise click.ClickException(
                "An account with ADMIN_EMAIL already exists; no account was changed."
            )

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role="admin",
            active=True,
        )
        db.session.add(user)
        db.session.commit()
        click.echo(f"Created admin account for {email}.")

    @app.get("/")
    def index():
        return jsonify(message="Tourisense backend")

    @app.get("/api/health")
    def health_check():
        return jsonify(
            status="ok",
            message="Tourisense backend is running",
        )

    @app.get("/api/health/db")
    def database_health_check():
        try:
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return jsonify(status="error", database="disconnected"), 503

        return jsonify(status="ok", database="connected")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
