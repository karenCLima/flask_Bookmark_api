from flask import Flask, redirect, jsonify
import os
from src.auth import auth_ns
from src.bookmarks import bookmarks_ns
from src.database import db, Bookmark
from flask_jwt_extended import JWTManager
from src.constants.http_status_code import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from flask_restx import Api

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    secret_key = os.environ.get("SECRET_KEY")
    jwt_secret_key = os.environ.get("JWT_SECRET_KEY")

    if not secret_key or not jwt_secret_key:
        raise ValueError("SECRET_KEY and JWT_SECRET_KEY must be set in environment variables")

    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=secret_key,
            SQLALCHEMY_DATABASE_URI=os.environ.get("SQLALCHEMY_DB_URI"),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY=jwt_secret_key,
        )
    else:
        app.config.from_mapping(test_config)

    db.app = app
    db.init_app(app)

    JWTManager(app)

    # Definindo o esquema de segurança para o Swagger
    authorizations = {
        'BearerAuth': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Please enter a valid JWT token'
        }
    }

    # Criando o objeto Api com as definições de segurança
    api = Api(app, 
              version='1.0', 
              title='Bookmarks API', 
              description='API for managing bookmarks',
              security='BearerAuth',
              authorizations=authorizations
             )

    # Registrar namespaces
    api.add_namespace(auth_ns)
    api.add_namespace(bookmarks_ns)

    # Define a new endpoint for redirecting URLs
    @app.route('/<short_url>', methods=['GET'])
    def redirect_to_url(short_url):
        bookmark = Bookmark.query.filter_by(short_url=short_url).first_or_404()

        if bookmark:
            bookmark.visits += 1
            db.session.commit()

            return redirect(bookmark.url)

    # Error handling
    @app.errorhandler(HTTP_404_NOT_FOUND)
    def handle_404(e):
        return jsonify({"error": "Not Found"}), HTTP_404_NOT_FOUND

    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def handle_500(e):
        return jsonify({"error": "Something went wrong. We are working on it"}), HTTP_500_INTERNAL_SERVER_ERROR

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle general exceptions"""
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), HTTP_500_INTERNAL_SERVER_ERROR

    return app
