from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Dropbox(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String)
    secret = db.Column(db.String)
    access_token = db.Column(db.String)
    file_location = db.Column(db.String)
    cursor = db.Column(db.String)


class Pushbullet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String)


class ToDo(db.Model):
    __tablename__ = 'todo'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String)
    date_time = db.Column(db.DateTime)
