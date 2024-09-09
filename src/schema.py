from marshmallow import Schema, fields

class BookmarkSchema(Schema):
    id = fields.Int()
    short_url = fields.Str()
    url = fields.Str()
    body = fields.Str()
    visits = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()