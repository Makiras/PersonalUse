from datetime import date, datetime
from hashlib import md5

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


SALT = md5(str(datetime.now()).encode('utf-8')).hexdigest()
LAST_STATUS_REFRESH_ALL_COOKIES = {'TIME': datetime.now(), 'USER_STATUS': None}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///webManager.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

web_db = SQLAlchemy(app)

class UserInfo(web_db.Model):
    id = web_db.Column(web_db.Integer, primary_key=True)
    uid = web_db.Column(web_db.String())
    status = web_db.Column(web_db.String())
    name = web_db.Column(web_db.String())
    cookies = web_db.Column(web_db.String())
    timestamp = web_db.Column(web_db.DateTime, default=datetime.now)

    def __init__(self, uid, status):
        self.uid = uid
        self.status = status

    def __repr__(self):
        return '<QrUrl: %r %r>' % (self.uid, self.status)