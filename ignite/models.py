from flask_sqlalchemy import SQLAlchemy
from flask_admin import form

from sqlalchemy.event import listens_for
from sqlalchemy.schema import UniqueConstraint

import os
import datetime

db = SQLAlchemy()

file_path = os.path.join(os.path.dirname(__file__), 'static/upload')
try:
    os.mkdir(file_path)
except OSError:
    pass


# Create models
class Houses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)
    desc = db.Column(db.String(1000))
    shortdesc = db.Column(db.String(140))
    captain = db.Column(db.String(100))
    color = db.Column(db.String(6))
    imagepath = db.Column(db.String(128))
    markers = db.relationship('Markers', backref=db.backref('house'))
    users = db.relationship('Users', backref=db.backref('house'))

    def __str__(self):
        return self.name

    @property
    def points(self):
        points = 0
        for user in self.users:
            if user.points:
                points = points + user.points
        return points


class Markers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    point_value = db.Column(db.Integer, nullable=False)
    house_id = db.Column(db.Integer, db.ForeignKey(Houses.id), nullable=True)
    in_current_use = db.Column(db.Boolean, default=True)
    is_hidden = db.Column(db.Boolean)
    batch = db.Column(db.String(20))
    location = db.Column(db.String(15))
    scans = db.relationship('Scans', backref=db.backref('marker'),
                            cascade='all, delete, delete-orphan, save-update')

    def __str__(self):
        return self.name


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uname = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    pwhash = db.Column(db.Binary(60), nullable=False)
    house_id = db.Column(db.Integer, db.ForeignKey(Houses.id), nullable=False)
    points = db.Column(db.Integer, default=0)
    scans = db.relationship('Scans', backref=db.backref('user'),
                            cascade='all, delete, delete-orphan')

    def __str__(self):
        return self.uname


class Scans(db.Model):
    __table_args__ = (UniqueConstraint(
        'user_id', 'marker_id', name='_user_marker_uc'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(Users.id), nullable=False)
    marker_id = db.Column(db.Integer, db.ForeignKey(Markers.id),
                          nullable=False)
    point_value = db.Column(db.Integer, nullable=True)
    scan_time = db.Column(db.DateTime, nullable=False,
                          default=datetime.datetime.utcnow)

    def __str__(self):
        return self.user.uname + " scanned '" + self.marker.name + "'"


class Pages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    route = db.Column(db.String(15), unique=True, nullable=False)
    content = db.Column(db.String(12000), nullable=False)
    custom_layout = db.Column(db.Boolean, default=False)
    no_wrap = db.Column(db.Boolean, default=False)

    def __str__(self):
        return self.title


# Database Triggers
@listens_for(Scans, 'before_insert')
def add_points(mapper, connection, target):
    """ Adds points to a user after they scan something """
    if target.user.house_id == target.marker.house_id:
        scan_points = target.marker.point_value * 2
    else:
        scan_points = target.marker.point_value

    target.point_value = scan_points
    user_points = target.user.points + scan_points

    connection.execute("UPDATE users SET points = ? WHERE id = ?",
                       (user_points, target.user_id))


@listens_for(Scans, 'before_delete')
def remove_points(mapper, connection, target):
    """ Removes points from a user after a scan is deleted """
    user_points = target.user.points - int(target.point_value or 1)
    connection.execute("UPDATE users SET points = ? WHERE id = ?",
                       (user_points, target.user_id))


@listens_for(Houses, 'after_delete')
def del_image(mapper, connection, target):
    if target.imagepath:
        # Delete image
        try:
            os.remove(os.path.join(file_path, target.path))
        except OSError:
            pass

        # Delete thumbnail
        try:
            os.remove(os.path.join(file_path,
                                   form.thumbgen_filename(target.path)))
        except OSError:
            pass
