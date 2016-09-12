from flask_sqlalchemy import SQLAlchemy
from flask_admin import AdminIndexView, BaseView, expose
from flask import session, flash, redirect, url_for, request, send_from_directory
from hashids import Hashids
from flask import current_app

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


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return session.get('ad_login') # This does the trick rendering the view only if the user is authenticated

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            flash("You must be logged in to access this feature")
            return redirect(url_for('admin_login', next=request.url))

class QRGenView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

    def gen_zip(self, markers):
        import pyqrcode
        from zipfile import ZipFile
        import io, os

        ## This ensures that it is in the package directory rather than just cwd
        __location__ = self.get_location()
        print(__location__)
        zipper = ZipFile(os.path.join(__location__, 'markers.zip'), 'w')
        hashid = Hashids(min_length=6, salt=current_app.config['HASHID_KEY'])
        for i in range(0, len(markers)):
            marker = markers[i]
            marker.url = url_for('scan_marker', scan_id=hashid.encode(marker.id), _external=True)
            buffer = io.BytesIO()
            qrcode = pyqrcode.create(marker.url)
            qrcode.svg(buffer, scale=5, background="white")
            zipper.writestr(str(marker.id)+"-"+marker.name+"-"+str(marker.houses.name)+".svg", buffer.getvalue())
        zipper.close()

    @expose('/gen', methods=['POST'])
    def generate_zip(self):
        markers = Markers.query.all()
        self.gen_zip(markers)
        flash("Currently generating .zip in the background, please wait a few minutes")
        return redirect(url_for('admin.index'))

    @expose('/download', methods=['POST'])
    def download_zip(self):
        try:

            __location__ = self.get_location()
            print(__location__)
            return send_from_directory(__location__, 'markers.zip', as_attachment=True)
        except:
            flash("Please generate the .zip first")
            return redirect(url_for('admin.index'))

    def get_location(self):
        import os
        return os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
