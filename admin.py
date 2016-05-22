from flask import Blueprint, request, session, redirect, url_for, \
    abort, render_template, flash, send_from_directory
from decorators import async, ad_login_req
import MySQLdb
from hashids import Hashids


admin = Blueprint('admin', __name__)
admin.config = {}

## Overide to allow access to configuration values
@admin.record
def record_params(setup_state):
  app = setup_state.app
  admin.config = dict([(key,value) for (key,value) in app.config.iteritems()])


@admin.route('/')
@ad_login_req
def admin_main():
    return render_template('admin.html')

@admin.route('/login', methods=['POST', 'GET'])
def admin_login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if username == admin.config['ADMIN_UNAME'] and password == admin.config['ADMIN_PWORD']:
            session['ad_login'] = True
            return redirect('admin')
        else:
            flash("Incorrect login details")
    return render_template('admin-login.html')

@admin.route('/logout', methods=['POST', 'GET'])
@ad_login_req
def admin_logout():
    session.pop('ad_login', None)
    return redirect(url_for('index'))

@async
@admin.route('/download', methods=['POST'])
@ad_login_req
def download_zip():
    try:
        import os
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        return send_from_directory(__location__, 'markers.zip', as_attachment=True)
    except:
        flash("Please generate the .zip first")
        return redirect(url_for('admin'))

@async
@admin.route('/gen', methods=['POST'])
@ad_login_req
def generate_zip():
    markers = query_db("SELECT * FROM markers_with_houses")
    generate_zip(markers)
    flash("Currently generating .zip in the background, please wait a few minutes")
    return redirect(url_for('admin.admin_main'))

def generate_zip(markers):
    import pyqrcode
    from zipfile import ZipFile
    import io, os
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    zipper = ZipFile(os.path.join(__location__, 'markers.zip'), 'w')
    #marker["url"] = "https://amelia.geek.nz/s/" + str(marker['id'])
    hashid = Hashids(min_length=6, salt=admin.config['HASHID_KEY'])
    for i in range(0, len(markers)):
        marker = markers[i]
        marker["url"] = url_for('scan_marker', scan_id=hashid.encode(marker["id"]), _external=True)
        buffer = io.BytesIO()
        qrcode = pyqrcode.create(marker["url"])
        qrcode.svg(buffer, scale=5, background="white")
        zipper.writestr(str(marker["id"])+"-"+marker["name"]+"-"+str(marker["house"])+".svg", buffer.getvalue())
    zipper.close()

# Database shisazt
def connect_db():
    return MySQLdb.connect(host=admin.config['DB_HOST'],    # your host, usually localhost
                         user=admin.config['DB_USER'],         # your username
                         passwd=admin.config['DB_PASS'],  # your password
                         db=admin.config['DB_NAME'])        # name of the data base

def query_db(query, values=0):
    """ Query DB & commit """
    db = connect_db()
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    if isinstance(values, (list, tuple)):
        cur.execute(query, values)
    else:
        cur.execute(query)
    output = cur.fetchall()
    db.commit()
    db.close()
    return output
