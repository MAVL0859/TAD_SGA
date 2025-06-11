from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import os
from app.infrastructure.config import Config
from flask_jwt_extended import exceptions as jwt_exceptions
from jwt.exceptions import ExpiredSignatureError
from flask import jsonify

# --- Infrastructure ---
db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = app.config['SECRET_KEY']

    db.init_app(app)
    jwt.init_app(app)

    # --- HANDLERS DE ERRORES JWT ---
    @app.errorhandler(jwt_exceptions.NoAuthorizationError)
    def handle_no_auth(e):
        return jsonify(msg='Token de autenticación faltante o mal formado'), 401

    @app.errorhandler(jwt_exceptions.InvalidHeaderError)
    def handle_invalid_header(e):
        return jsonify(msg='Header Authorization inválido'), 401

    @app.errorhandler(ExpiredSignatureError)
    def handle_expired_token(e):
        return jsonify(msg='Token expirado'), 401

    @app.errorhandler(jwt_exceptions.JWTDecodeError)
    def handle_jwt_decode(e):
        return jsonify(msg='Token JWT inválido'), 401

    @app.errorhandler(jwt_exceptions.WrongTokenError)
    def handle_wrong_token(e):
        return jsonify(msg='Tipo de token incorrecto'), 401

    @app.errorhandler(jwt_exceptions.RevokedTokenError)
    def handle_revoked_token(e):
        return jsonify(msg='Token revocado'), 401

    # Importar blueprints de interface
    from app.interface.public import public_bp
    from app.interface.auth import auth_bp
    from app.interface.admin import admin_bp
    from app.interface.student import student_bp
    from app.interface.teacher import teacher_bp
    from app.interface.dashboard import dashboard_bp
    from app.interface.course import course_bp
    from app.interface.enroll import enroll_bp
    from app.interface.assignment import assignment_bp
    from app.interface.submission import submission_bp

    # REGISTRA PRIMERO EL BLUEPRINT PÚBLICO
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(course_bp, url_prefix='/courses')
    app.register_blueprint(enroll_bp, url_prefix='/enrollments')
    app.register_blueprint(assignment_bp, url_prefix='/assignments')
    app.register_blueprint(submission_bp, url_prefix='/submissions')

    return app

# --- Entry point ---
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
