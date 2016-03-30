from flask import Flask, request, session, redirect, url_for, \
    abort, render_template, flash, send_from_directory
import MySQLdb
from hashids import Hashids
from flask.ext.bcrypt import Bcrypt
from functools import wraps
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.config.from_pyfile('application.cfg', silent=True)
bcrypt = Bcrypt(app)


@app.route('/')
def index():
    return render_template('index.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Must be logged in.')
            #TODO: use of nextu incl post
            return redirect(url_for('login', nextu=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
@app.route('/login/redirect/<path:nextu>', methods=['GET', 'POST'])
def login(nextu=None):
    error = None
    if session.get('username'):
        return redirect(url_for('index'))
    if request.method == "POST":
        username = clean_str(request.form['username'])
        password = clean_str(request.form['password'])
        if '@' in username:
            data = query_db('SELECT * FROM users WHERE email = %s',[username])
        else:
            data = query_db('SELECT * FROM users WHERE uname = %s',[username])

        if len(data) == 0:
            error = 'Invalid username'
        elif bcrypt.check_password_hash(data[0]['pwhash'], password):
            session['username'] = data[0]['uname']
            session['user_id'] = data[0]['id']
            flash('You were logged in')
            if nextu:
                return redirect(nextu)
            return redirect(url_for('index'))
        else:
            error = 'Invalid Password'
    return render_template('login.html', error=error, nextu=nextu)

@app.route('/adduser', methods=['GET', 'POST'])
def add_user():
    # TODO: add better error handling
    error = None
    if session.get('username'):
        return redirect(url_for('index'))
    if request.method == "POST":
        username = request.form['username']
        password = clean_str(request.form['password'])
        house_id = request.form['house']
        if not is_clean_username(username):
            error = "Username must contain only alpha-numeric characters, and must be between 5 and 12 characters"
        elif not email_validate(request.form['email']):
            error = "Invalid Email Address"
        elif username and password: ## basically not null
            #return str(username) + " " + str(password)
            try:
                data = query_db('INSERT INTO users(uname, pwhash, email, house_id) values(%s, %s, %s, %s)',[username, bcrypt.generate_password_hash(password), request.form['email'], house_id])
                session['username'] = username
                session['user_id'] = query_db('SELECT id FROM users where uname = %s',[username])[0]['id']
                flash('You were logged in')
                return redirect(url_for('index'))
            except MySQLdb.Error, e:
                if e.args[0] == 1062:
                    if 'email' in e.args[1]:
                        error = "Email already in use. You may already have an account. Try the forgot password link below"
                    elif 'uname' in e.args[1]:
                        error = "Username already in use. Be more creative"
                else:
                    error = "Database Error. %s %s" % (e.args[0], e.args[1])
        else:
            error = "Invalid Username Or Password"
    houses = query_db("SELECT * FROM houses")
    return render_template('adduser.html', error=error, houses=houses)


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route('/forgotpass', methods=['GET','POST'])
def lost_password():
    if session.get('username'):
        flash("You've already logged in!!")
        return redirect(url_for('index'))

    if request.method == "POST":
        email = request.form['email']
        # check email address in db and get username
        try:
            username = query_db("SELECT * FROM users WHERE email = %s", [email])[0]['uname']
        except:
            flash("Email Address not found")
            return render_template('lostpass.html')

        ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])
        token = ts.dumps(email)
        confirm_url = url_for("resetpassword", serial_tag=token, _external=True)

        msg = render_template("lostpassemail.html", confirm_url=confirm_url, username=username)
        send_email(email, msg)
        flash("Email Sent to " + email)
        return redirect(url_for('login'))

    return render_template('lostpass.html')

@app.route('/resetpassword/<serial_tag>', methods=['GET','POST'])
def resetpassword(serial_tag):
    ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    try:
        email = ts.loads(serial_tag, max_age=14400)
        username = query_db("SELECT * FROM users WHERE email = %s", [email])[0]['uname']
    except:
        abort(404)

    if request.method == "POST":
        password = request.form['password']
        if password == request.form['confpassword']:
            try:
                data = query_db('UPDATE users SET pwhash = %s WHERE email = %s', [bcrypt.generate_password_hash(password), email])
            except:
                abort(500)
            flash("Password has been reset")
            return redirect(url_for('login'))
        flash("Passwords do not match")
    return render_template("resetpass.html",username=username, url=request.url)

def send_email(toadrr,message,fromaddr="amelia.stuffed@gmail.com", subject="Reset Password|Ignite"):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = "Ignite Admin"
    msg['To'] = toadrr
    part2 = MIMEText(message, 'html')
    msg.attach(part2)

    username = app.config['EMAIL_USER']
    password = app.config['EMAIL_PASS']

    # Sending the mail

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username,password)
    server.sendmail(fromaddr, app.config['TEST_EMAIL'],msg.as_string())
    server.quit()


@app.route('/user/<int:user_id>')
def show_user_profile(user_id):
    # show the user profile for that user
    try:
        user = query_db("SELECT * FROM users_with_house WHERE id = %s", [user_id])[0]
    except MySQLdb.Error, e:
        abort(404)
    except IndexError, e:
        abort(404)
    return render_template("user.html", user=user)

@app.route('/torch/<int:marker_id>')
def show_marker(marker_id):
    # show the marker profile
    try:
        marker = query_db("SELECT * FROM markers_with_houses WHERE id = %s", [marker_id])[0]
    except MySQLdb.Error, e:
        abort(404)
    except IndexError, e:
        abort(404)
    return render_template("marker.html", marker=marker)

@app.route('/house/<int:house_id>')
def show_house(house_id):
    # show the user profile for that user
    try:
        house = query_db("SELECT * FROM houses WHERE id = %s", [house_id])[0]
    except MySQLdb.Error, e:
        abort(404)
    except IndexError, e:
        abort(404)
    return render_template("house.html", house=house)

@app.route('/scan/<scan_id>')
@login_required
def scan_marker(scan_id):
    hashid = Hashids(min_length=6, salt=app.config['HASHID_KEY'])
    try:
        marker_id = hashid.decode(scan_id)[0]
    except IndexError:
        abort(404)
    try:
        asas = query_db("INSERT INTO scans (user_id, marker_id) values(%s, %s)", [str(session.get('user_id')), str(marker_id)])
    except MySQLdb.Error, e:
        if e.args[0] == 1452:
            abort(404)
        elif e.args[0] == 1062:
            flash("You've already scanned this torch.")
        else:
            flash("Database Error. %s %s" % (e.args[0], e.args[1]))

    return redirect(url_for("show_marker", marker_id=marker_id))

## Context Processors
@app.context_processor
def utility_processor():
    def recent_scans(column="all", wid=None, amount=20):
        # TODO: date-timehandeling
        data = []
        if(column == "user"):
            data = query_db("SELECT * FROM scan_info WHERE user_id = %s order by scan_time asc limit 20", [wid])
        elif(column == "house"):
            data = query_db("SELECT * FROM scan_info WHERE uhouse_id = %s order by scan_time asc limit 20", [wid])
        elif(column == "marker"):
            data = query_db("SELECT * FROM scan_info WHERE marker_id = %s order by scan_time asc limit 20", [wid])
        else:
            data = query_db("SELECT * FROM scan_info order by scan_time asc limit 20")
        return render_template("recent_scans.html", scans=data)

    return dict(recent_scans=recent_scans)

## Wrappers for login (Must be defined before use)
def ad_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('ad_login'):
            flash("Must be logged in as admin for this.")
            abort(401)
            #return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@ad_login_req
def admin():
    return render_template('admin.html')

@app.route('/admin/login', methods=['POST', 'GET'])
def admin_login():
    if request.method == "POST":
        username = clean_str(request.form['username'])
        password = clean_str(request.form['password'])
        if username == app.config['ADMIN_UNAME'] and password == app.config['ADMIN_PWORD']:
            session['ad_login'] = True
            return redirect('admin')
        else:
            flash("Incorrect login details")
    return render_template('admin-login.html')

@app.route('/admin/logout', methods=['POST', 'GET'])
@ad_login_req
def admin_logout():
    session.pop('ad_login', None)
    return redirect(url_for('index'))

@app.route('/admin/download', methods=['POST'])
@ad_login_req
def download_zip():
    return send_from_directory('',
                               'markers.zip', as_attachment=True)# and redirect(url_for('admin'))

@app.route('/admin/gen', methods=['POST'])
@ad_login_req
def generate_zip():
    markers = query_db("SELECT * FROM markers_with_houses")
    generate_zip(markers)
    return redirect(url_for('admin'))

def generate_zip(markers):
    import pyqrcode
    from zipfile import ZipFile
    import io

    zipper = ZipFile('markers.zip', 'w')
    #marker["url"] = "https://amelia.geek.nz/s/" + str(marker['id'])
    hashid = Hashids(min_length=6, salt=app.config['HASHID_KEY'])
    for i in range(0, len(markers)):
        marker = markers[i]
        marker["url"] = url_for('scan_marker', scan_id=hashid.encode(marker["id"]), _external=True)
        buffer = io.BytesIO()
        qrcode = pyqrcode.create(marker["url"])
        qrcode.svg(buffer, scale=5, background="white")
        marker["color"] = "black"
        svgtext = buffer.getvalue()[:-7] +  """<text x="20" y="200"  font-family="Verdana" fill=\"""" + marker["color"]  + "\">" + marker["name"] + " | " + str(marker["point_value"]) + "</text>"  + "</svg>"

        zipper.writestr(str(marker["id"])+".svg", svgtext)
    zipper.close()


## Error Handlers
@app.errorhandler(404)
def error_404(error):
    return render_template('errorpage.html', errorcode="404", message="Page not found on this server. Maybe check the URL?"), 404

@app.errorhandler(401)
def error_401(error):
    return render_template('errorpage.html', errorcode="401", message="Login brah. Unauthorised."), 401

@app.errorhandler(405)
def error_405(error):
    return render_template('errorpage.html', errorcode="405", message="What are you even trying to do? Wrong method"), 405

@app.errorhandler(500)
def error_401(error):
    return render_template('errorpage.html', errorcode="500", message="Error (sorry, contact the site admins for more info)"), 500


# Database shisazt
def connect_db():
    return MySQLdb.connect(host=app.config['DB_HOST'],    # your host, usually localhost
                         user=app.config['DB_USER'],         # your username
                         passwd=app.config['DB_PASS'],  # your password
                         db=app.config['DB_NAME'])        # name of the data base

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

### Users More like losers amirite?
# TODO: this, better, less convoluted
def clean_str(s):
    try:
        s.decode('ascii')
    except:
        return False
    ## Check For html
    return s

def is_clean_username(s):
    return s.isalnum() and len(s) >= 5 and len(s) <= 12

def bad_password_check(s):
    if(len(clean_str(s)) >= 5):
        return clean_str(s)
    return False

def email_validate(s):
    import re
    #[^@]+@[^@]+\.[^@]+
    return re.match("[^@]+@[^@]+\.[^@]+", s) and clean_str(s)

if __name__ == '__main__':
    app.run()
