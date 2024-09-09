from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from src.constants.http_status_code import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_200_OK
import validators
from src.database import User, db
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

auth_ns = Namespace('auth', description='Authentication related operations')

register_model = auth_ns.model('Register', {
    'username': fields.String(required=True, description='Username for registration'),
    'email': fields.String(required=True, description='Email address for registration'),
    'password': fields.String(required=True, description='Password for registration')
})

login_model = auth_ns.model('Login', {
    'email': fields.String(required=True, description='Email address for login'),
    'password': fields.String(required=True, description='Password for login')
})

@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(register_model)
    def post(self):
        username = request.json.get('username')
        email = request.json.get('email')
        password = request.json.get('password')

        if len(password) < 6:
            return {'error': "Password is too short"}, HTTP_400_BAD_REQUEST
        
        if len(username) < 3:
            return {'error': "Username is too short"}, HTTP_400_BAD_REQUEST
        
        if not username.isalnum() or " " in username:
            return {'error': "Username should be alphanumeric, also no spaces"}, HTTP_400_BAD_REQUEST
        
        if not validators.email(email):
            return {'error': "Email is not valid"}, HTTP_400_BAD_REQUEST
        
        if User.query.filter_by(email=email).first() is not None:
            return {'error': "Email is taken"}, HTTP_409_CONFLICT
        
        if User.query.filter_by(username=username).first() is not None:
            return {'error': "Username is taken"}, HTTP_409_CONFLICT
        
        pwd_hash = generate_password_hash(password)
        user = User(username=username, password=pwd_hash, email=email)
        
        db.session.add(user)
        db.session.commit()
        
        return {'message': "User created", 'user': {'username': username, 'email': email}}, HTTP_201_CREATED

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    def post(self):
        email = request.json.get('email', "")
        password = request.json.get('password', "")
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            refresh = create_refresh_token(identity=user.id)
            access = create_access_token(identity=user.id)
            
            return {'user': {'refresh': refresh, 'access': access, 'username': user.username, 'email': user.email}}, HTTP_200_OK
        
        return {'error': 'Wrong credentials'}, HTTP_401_UNAUTHORIZED

@auth_ns.route('/me')
class Me(Resource):
    @jwt_required()
    @auth_ns.doc(security='BearerAuth') 
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        return {'username': user.username, 'email': user.email}, HTTP_200_OK

@auth_ns.route('/token/refresh')
class RefreshToken(Resource):
    @jwt_required(refresh=True)
    @auth_ns.doc(security='BearerAuth') 
    def get(self):
        identity = get_jwt_identity()
        access = create_access_token(identity=identity)
        return {'access': access}, HTTP_200_OK
