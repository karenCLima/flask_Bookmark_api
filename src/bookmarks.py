from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from src.database import Bookmark, db
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.constants.http_status_code import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, HTTP_201_CREATED, HTTP_409_CONFLICT, HTTP_204_NO_CONTENT
import validators
import logging
from src.schema import BookmarkSchema

bookmark_schema = BookmarkSchema(many=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bookmarks_ns = Namespace('bookmarks', description='Bookmarks related operations')

bookmark_model = bookmarks_ns.model('Bookmark', {
    'body': fields.String(required=True, description='A short description of bookmark'),
    'url': fields.String(required=True, description='Full URL for the bookmark')
})

bookmark_response_model = bookmarks_ns.model('BookmarkResponse', {
    'id': fields.Integer(description='ID of the bookmark'),
    'short_url': fields.String(description='Short URL of the bookmark'),
    'url': fields.String(description='Full URL of the bookmark'),
    'body': fields.String(description="A short description of bookmark"),
    'visits': fields.Integer(description='Number of visits to the bookmark'),
    'created_at': fields.DateTime(description="Date of creation"),
    'updated_at': fields.DateTime(description="Date of update")
})

# def serialize_bookmark(bookmark):
#     return {
#         'id': bookmark.id,
#         'short_url': bookmark.short_url,
#         'url': bookmark.url,
#         'body': bookmark.body,
#         'visits': bookmark.visits,
#         'created_at': bookmark.created_at.isoformat() if bookmark.created_at else None,
#         'updated_at': bookmark.updated_at.isoformat() if bookmark.updated_at else None
#     }


@bookmarks_ns.route('/')
class BookmarkList(Resource):
    @jwt_required()
    @bookmarks_ns.doc(security='BearerAuth')
    #@bookmarks_ns.marshal_with(bookmark_response_model, as_list=True)
    def get(self):
        current_user = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)

        bookmarks = Bookmark.query.filter_by(user_id=current_user).paginate(page=page, per_page=per_page)
        # serialized_bookmarks = [serialize_bookmark(bookmark) for bookmark in bookmarks.items]
        data = bookmarks.items
        
        serialized_data = bookmark_schema.dump(data)
        logger.info(f"Serialized bookmarks data: {serialized_data}")

        meta = {
            'page': bookmarks.page,
            'pages': bookmarks.pages,
            'total_count': bookmarks.total,
            'prev_page': bookmarks.prev_num,
            'next_page': bookmarks.next_num,
            'has_next': bookmarks.has_next,
            'has_prev': bookmarks.has_prev
        }

        return {'data': serialized_data, 'meta': meta}, HTTP_200_OK

    @jwt_required()
    @bookmarks_ns.doc(security='BearerAuth')
    @bookmarks_ns.expect(bookmark_model)
    @bookmarks_ns.marshal_with(bookmark_response_model)
    def post(self):
        current_user = get_jwt_identity()
        data = bookmarks_ns.payload
        body = data['body']
        url = data['url']

        if not validators.url(url):
            return {'error': "Enter a valid url"}, HTTP_400_BAD_REQUEST

        if Bookmark.query.filter_by(url=url).first():
            return {'error': 'URL already exists'}, HTTP_409_CONFLICT

        bookmark = Bookmark(url=url, body=body, user_id=current_user)
        db.session.add(bookmark)
        db.session.commit()
        print(bookmark.url)

        return bookmark, HTTP_201_CREATED

@bookmarks_ns.route('/<int:id>')
class BookmarkResource(Resource):
    @jwt_required()
    @bookmarks_ns.doc(security='BearerAuth')
    @bookmarks_ns.marshal_with(bookmark_response_model)
    def get(self, id):
        current_user = get_jwt_identity()
        bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()

        if not bookmark:
            return {'message': 'Item not found'}, HTTP_404_NOT_FOUND

        return bookmark, HTTP_200_OK

    @jwt_required()
    @bookmarks_ns.doc(security='BearerAuth') 
    def delete(self, id):
        current_user = get_jwt_identity()
        bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()

        if not bookmark:
            return {'message': 'Item not found'}, HTTP_404_NOT_FOUND

        db.session.delete(bookmark)
        db.session.commit()

        return '', HTTP_204_NO_CONTENT
    
    @bookmarks_ns.doc(security='BearerAuth')
    @jwt_required()  # Protege a rota com JWT
    @bookmarks_ns.expect(bookmark_model)  # Espera o modelo Bookmark
    @bookmarks_ns.response(200, 'Bookmark updated successfully')
    @bookmarks_ns.response(404, 'Bookmark not found')
    @bookmarks_ns.marshal_with(bookmark_response_model)
    def put(self, id):
        current_user = get_jwt_identity()
        bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()

        if not bookmark:
            return {'message': 'Item not found'}, HTTP_404_NOT_FOUND

        body = request.json.get('body', '')
        url = request.json.get('url', '')

        if not validators.url(url):
            return {'error': "Enter a valid url"}, HTTP_400_BAD_REQUEST

        bookmark.url = url
        bookmark.body = body
        db.session.commit()

        return bookmark, HTTP_200_OK
    
@bookmarks_ns.route('/stats')
class BookmarkStatsResource(Resource):
    @bookmarks_ns.doc(security='BearerAuth')
    @bookmarks_ns.marshal_with(bookmark_response_model)
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        items = Bookmark.query.filter_by(user_id=current_user).all()
        data = [{'visits': item.visits, 'url': item.url, 'id': item.id, 'short_url': item.short_url} for item in items]

        return {'data': data}, HTTP_200_OK
