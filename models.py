from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Create models
class Houses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)
    desc = db.Column(db.String(1000))
    shortdesc = db.Column(db.String(140))
    captain = db.Column(db.String(100))
    color = db.Column(db.String(6))

    def __str__(self):
        return self.name

class Markers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)
    point_value = db.Column(db.Integer, nullable=False)
    house_id = db.Column(db.Integer, db.ForeignKey(Houses.id), nullable=True)
    in_current_use = db.Column(db.Boolean, default=True)
    is_hidden = db.Column(db.Boolean)
    batch = db.Column(db.String(20))
    location = db.Column(db.String(15))
    houses = db.relationship('Houses', backref=db.backref('Markers'))

    def __str__(self):
        return self.name

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uname = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    pwhash = db.Column(db.Binary(60), nullable=False)
    house_id = db.Column(db.Integer, db.ForeignKey(Houses.id), nullable=False)
    points = db.Column(db.Integer)
    houses = db.relationship('Houses', backref=db.backref('Users'))

    def __str__(self):
        return self.name
