from ShortenYourLink import db, ma
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash


app_dmn = 'https://shortenyourlink.herokuapp.com/'


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    orig_link = db.Column(db.String(500), nullable=False)
    domain_name = db.Column(db.String(100), nullable=False)
    random_sequence = db.Column(db.String(8), nullable=False, unique=True)
    link_owner = db.Column(db.Integer, default=0)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow(), nullable=False)
    link_tag = db.Column(db.String(32))

    def __repr__(self):
        return f'<Link {self.orig_link}>'


class LinkSchema(ma.Schema):
    class Meta:
        fields = ('id', 'orig_link', 'domain_name', 'random_sequence', 'link_owner', 'creation_date', 'link_tag')


link_schema = LinkSchema()
link_schemas = LinkSchema(many=True)


class Transitions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, nullable=False)
    link_id = db.Column(db.Integer, nullable=False)
    trans_time = db.Column(db.DateTime, nullable=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    registration_date = db.Column(db.DateTime)
    last_login_date = db.Column(db.DateTime)
    account_status = db.Column(db.Boolean, default=False)

    def get_token(self, life_time=24):
        link_life_time = timedelta(life_time)
        token = create_access_token(identity=self.id, expires_delta=link_life_time)
        return token

    @classmethod
    def authenticate(cls, login, password):
        user = cls.query.filter(cls.login == login).one()
        if not check_password_hash(user.password, password):
            return 'No user with this password', 400
        return user
