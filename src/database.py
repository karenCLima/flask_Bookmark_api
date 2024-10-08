from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import string
from sqlalchemy.orm import backref
import random

db = SQLAlchemy()


class User(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(80), unique=True, nullable=False)
    email=db.Column(db.String(120), unique=True, nullable=False)
    password=db.Column(db.Text(), nullable=False)
    created_at=db.Column(db.DateTime, default=datetime.now())
    updated_at=db.Column(db.DateTime, onupdate=datetime.now())
    bookmarks=db.relationship('Bookmark', backref="user")
    
    def __repr__(self) -> str:
        return 'User>>>{self.username}'
    
    
class Bookmark(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    body=db.Column(db.Text, nullable=True)
    url=db.Column(db.Text, nullable=True)
    short_url=db.Column(db.String(3), nullable=True)
    visits=db.Column(db.Integer, default=0)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at=db.Column(db.DateTime, default=datetime.now())
    updated_at=db.Column(db.DateTime, onupdate=datetime.now())
    
    def generate_short_characters(self):
        characters=string.digits+string.ascii_letters
        picked_chars=''.join(random.choices(characters, k=3))
        
        link=self.query.filter_by(short_url=picked_chars).first()
        
        if link:
            return self.generate_short_characters()
        else:
            return picked_chars
        
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.short_url=self.generate_short_characters()
    
    def __repr__(self) -> str:
        return f"Bookmark(id={self.id}, url={self.url}, short_url={self.short_url}, body={self.body}, visits={self.visits}, created_at={self.created_at}, updated_at={self.updated_at})"