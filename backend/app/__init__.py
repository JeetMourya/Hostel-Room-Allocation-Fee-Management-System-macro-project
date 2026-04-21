from flask import Flask
from flask_cors import CORS
from config import Config
from app.extensions import db, migrate, jwt

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register models so Alembic can detect them
    from app.models import User, Student, Room, Allocation, Fee, Complaint, Notice, Visitor, StudentVerification

    # Register blueprints (Controllers)
    # from app.controllers.health_controller import health_bp
    # app.register_blueprint(health_bp, url_prefix='/api')
    
    return app
