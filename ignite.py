from flask import Flask, request, session, redirect, url_for, \
    abort, render_template, flash
import MySQLdb
from hashids import Hashids

DEBUG = True
SECRET_KEY = 'development key'

app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if session.get('username'):
        return redirect(url_for('index'))

    ## TODO: allow entry by email address
    if request.method == "POST":
        username = clean_str(request.form['username'])
        password = clean_str(request.form['password'])
        if '@' in username:
            data = query_db('SELECT * FROM users WHERE email = %s',[username])
        else:
            data = query_db('SELECT * FROM users WHERE uname = %s',[username])

        if len(data) == 0:
            error = 'Invalid username'
        elif data[0]['pword'] == password:
            session['username'] = data[0]['uname']
            session['user_id'] = data[0]['id']
            flash('You were logged in')
            return redirect(url_for('index'))
        else:
            error = 'Invalid Password'
    return render_template('login.html', error=error)

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
                data = query_db('INSERT INTO users(uname, pword, email, house_id) values(%s, %s, %s, %s)',[username, password, request.form['email'], house_id])
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
        return redirect(url_for('index'))
    flash("Still working on it bro.")
    return redirect(url_for('login'))

@app.route('/user/<int:user_id>')
def show_user_profile(user_id):
    # show the user profile for that user
    try:
        user = query_db("SELECT * FROM users WHERE id = %s", [user_id])[0]
    except MySQLdb.Error, e:
        abort(404)
    except IndexError, e:
        abort(404)
    return render_template("user.html", user=user)

@app.route('/torch/<int:marker_id>')
def show_marker(marker_id):
    # show the marker profile
    try:
        marker = query_db("SELECT * FROM markers WHERE id = %s", [marker_id])[0]
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
def scan_marker(scan_id):
    if not session.get('user_id'):
        flash("Must be logged in to scan.")
        # TODO: Redriect Back
        return redirect(url_for("login"))
    hashid = Hashids(min_length=6)
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


# Database shisazt
def connect_db():
    return MySQLdb.connect(host="localhost",    # your host, usually localhost
                         user="ignite",         # your username
                         passwd="password",  # your password
                         db="ignite")        # name of the data base

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
