from flask import Flask, request, session, redirect, url_for, \
    abort, render_template, flash
from flask_bcrypt import Bcrypt
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from itsdangerous import URLSafeTimedSerializer
from hashids import Hashids
from sqlalchemy.exc import IntegrityError

from ignite.decorators import login_required
from ignite.models import db, Houses, Markers, Users, Pages, Scans
from ignite.admin_views import (MyAdminIndexView, QRGenView, MarkerView,
                                UserView, HouseView, APageView)
from ignite.utils import (clean_str, is_clean_username,
                          email_validate, send_email)
from collections import defaultdict
import datetime

app = Flask(__name__)
app.config.from_pyfile('application.cfg', silent=True)
bcrypt = Bcrypt(app)

admin = Admin(app, name="IGNITE Admin", index_view=MyAdminIndexView())
db.init_app(app)
admin.add_view(QRGenView(name='Generate QR codes', endpoint='gen'))
admin.add_view(UserView(Users, db.session))
admin.add_view(MarkerView(Markers, db.session))
admin.add_view(HouseView(Houses, db.session))
admin.add_view(APageView(Pages, db.session))
admin.add_view(ModelView(Scans, db.session))


@app.route('/adminlogin', methods=['POST', 'GET'])
def admin_login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if (username == app.config['ADMIN_UNAME'] and
                password == app.config['ADMIN_PWORD']):
            session['ad_login'] = True
            return redirect('admin')
        else:
            flash("Incorrect login details")
    return render_template('alogin.html')


@app.route('/adminlogout', methods=['POST', 'GET'])
def admin_logout():
    session.pop('ad_login', None)
    return redirect(url_for('index'))


@app.route('/')
def index():
    houses = Houses.query.all()
    return render_template('index.html', house_points=houses)


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
            data = Users.query.filter_by(email=username).all()
        else:
            data = Users.query.filter_by(uname=username).all()

        if len(data) == 0:
            error = 'Invalid username'
        elif bcrypt.check_password_hash(data[0]['pwhash'], password):
            session['username'] = data[0]['uname']
            session['user_id'] = data[0]['id']
            flash('You were logged in')
            if nextu:
                nextu = "http://" + nextu
                return redirect(nextu)
            return redirect(url_for('index'))
        else:
            error = 'Invalid Password'
    return render_template('login.html', error=error, nextu=nextu)


@app.route('/adduser', methods=['GET', 'POST'])
def add_user():
    # TODO: add better error handling
    error = None
    username = None
    email = None
    if session.get('username'):
        return redirect(url_for('index'))
    if request.method == "POST":
        username = request.form['username']
        password = clean_str(request.form['password'])
        house_id = request.form['house']
        email = request.form['email']

        if not is_clean_username(username):
            error = ("Username must contain only alpha-numeric characters, "
                     "and must be between 5 and 20 characters")
        elif not email_validate(email):
            error = "Invalid Email Address"
        elif username and password:
            try:
                new_user = Users(
                    uname=username,
                    pwhash=bcrypt.generate_password_hash(password),
                    email=email,
                    house_id=house_id)

                db.session.add(new_user)
                db.session.commit()

                session['username'] = username
                session['user_id'] = Users.query.filter_by(
                    uname=username).first().id

                flash('You were logged in id: %s' % session['user_id'])

                house = Houses.query.filter_by(id=house_id).first()
                msg = render_template("newaccount.html", username=username,
                                      email=email, house=house)
                send_email(email, msg, 'New Account Notification | Ignite')
                flash("Email Sent to " + email)
                return redirect(url_for('index'))
            except IntegrityError as e:
                print(e.args)
                if 'email' in str(e.args):
                    error = ("Email already in use. "
                             "You may already have an account. "
                             "Try the forgot password link below")
                elif 'uname' in str(e.args):
                    error = "Username already in use. Be more creative"
                else:
                    error = "Database Error. %s" % e.args
                db.session.rollback()
        else:
            error = "Invalid Username Or Password"
    houses = Houses.query.all()
    return render_template('adduser.html', error=error, houses=houses,
                           email=email, username=username)


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    flash('You were logged out')
    return redirect(url_for('index'))


@app.route('/forgotpass', methods=['GET', 'POST'])
def lost_password():
    if session.get('username'):
        flash("You've already logged in!!")
        return redirect(url_for('index'))

    if request.method == "POST":
        email = request.form['email']
        # check email address in db and get username
        try:
            user = Users.query.filter_by(email=email).first()
        except:
            flash("Email Address not found")
            return render_template('lostpass.html')

        ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])
        token = ts.dumps(email)
        confirm_url = url_for("resetpassword", serial_tag=token,
                              _external=True)

        msg = render_template("lostpassemail.html", confirm_url=confirm_url,
                              username=user.uname)
        send_email(email, msg, "Forgot Password? | Ignite")
        flash("Email Sent to " + email)
        return redirect(url_for('login'))

    return render_template('lostpass.html')


@app.route('/resetpassword/<serial_tag>', methods=['GET', 'POST'])
def resetpassword(serial_tag):
    ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    try:
        email = ts.loads(serial_tag, max_age=14400)
        user = Users.query.filter_by(email=email)
    except:
        abort(404)

    if request.method == "POST":
        password = request.form['password']
        if password == request.form['confpassword']:
            try:
                user.pwhash = bcrypt.generate_password_hash(password)
                db.session.add(user)
                db.commit()
            except:
                abort(500)
                db.session.rollback()

            flash("Password has been reset")
            return redirect(url_for('login'))
        flash("Passwords do not match")
    return render_template("resetpass.html", username=user.uname,
                           url=request.url)


@app.route('/user/<int:user_id>')
def show_user_profile(user_id):
    user = Users.query.filter_by(id=user_id).first_or_404()
    return render_template("user.html", user=user)


@app.route('/torch/<int:marker_id>')
def show_marker(marker_id):
    marker = Markers.query.filter_by(id=marker_id).first_or_404()
    return render_template("marker.html", marker=marker)


@app.route('/house/<int:house_id>')
def show_house(house_id):
    house = Houses.query.filter_by(id=house_id).first_or_404()
    return render_template("house.html", house=house)


@app.route('/scan/<scan_id>')
@login_required
def scan_marker(scan_id):
    hashid = Hashids(min_length=6, salt=app.config['HASHID_KEY'])
    try:
        marker_id = hashid.decode(scan_id)[0]
        marker = Markers.query.filter(id=marker_id).first_or_404()
    except:
        abort(404)

    if marker.in_current_use:
        try:
            scan = Scans(user_id=session.get('user_id'),
                         marker_id=marker.id)
            db.session.add(scan)
            db.commit()
            flash("Congratulations on scanning this marker!")

        except IntegrityError as e:
            print(e.args)
            flash("You've already scanned this torch.")

    else:
        flash("Unfortunatley this marker is incative at this time and "
              "therefore you cannot scan it.")

    return redirect(url_for("show_marker", marker_id=marker_id))


# Context Processors
@app.context_processor
def utility_processor():
    def recent_scans(column="all", wid=None, amount=20):
        # TODO: date-timehandeling
        data = []
        if column == "user":
            data = Scans.query.filter_by(user_id=wid).order_by(
                Scans.scan_time.desc()).limit(20)
        elif column == "house":
            data = Scans.query.filter(
                Scans.user.has(house_id=wid)).order_by(
                Scans.scan_time.desc()).limit(20)
        elif column == "marker":
            data = Scans.query.filter_by(marker_id=wid).order_by(
                Scans.scan_time.desc()).limit(20)
        else:
            data = Scans.query.order_by(
                Scans.scan_time.desc()).limit(20)
        return render_template("recent_scans.html", scans=data)

    def generate_graph():
        houses = Houses.query.all()
        graph_data = defaultdict(dict)

        try:
            lowest_hour = Scans.query.order_by(
                Scans.scan_time.asc()).first().scan_time
        except Exception:
            return "No Scans Yet. </br>"
        highest_hour = Scans.query.order_by(
            Scans.scan_time.desc()).first().scan_time

        for house in houses:
            house_points = 0
            current_hour = lowest_hour
            print(house.name)
            while current_hour <= highest_hour:
                next_hour = current_hour + datetime.timedelta(hours=1)
                scans = Scans.query.filter(
                    Scans.scan_time.between(current_hour, next_hour)).filter(
                    Scans.user.has(house_id=house.id)).all()
                no_cur_hour_points = sum([scan.point_value for scan in scans])
                house_points += no_cur_hour_points
                graph_data[current_hour][house.name] = house_points

                current_hour = next_hour

        import operator
        graph_data = sorted(graph_data.items(), key=operator.itemgetter(0))
        return render_template("time-graph.html", houses=houses,
                               graph_data=graph_data)

    def get_pages():
        return Pages.query.all()

    def get_houses():
        return Houses.query.all()

    return dict(recent_scans=recent_scans, generate_graph=generate_graph,
                get_pages=get_pages, get_houses=get_houses)


# PAGES
@app.route('/housegraph')
def housegraph():
    return render_template('housegraph.html')


@app.route('/recent_scans_page')
def recent_scans_page():
    return render_template('recent_scans_page.html')


@app.route('/torch_registry')
def torch_registry():
    torches = Markers.query.filter_by(is_hidden=False)
    return render_template('torch_registry.html', torches=torches)


@app.route('/topusers')
def topusers():
    users = Users.query.order_by(Users.points.desc()).limit(30)
    return render_template('topuser.html', users=users)


# Custom Pages
@app.route('/<route>')
def db_page(route):
    page = Pages.query.filter_by(route=route).first()
    return render_template('page.html', page=page)


# Error Handlers
@app.errorhandler(404)
def error_404(error):
    return render_template('errorpage.html', errorcode="404",
                           message="Page not found on this server. "
                           "Maybe check the URL?"), 404


@app.errorhandler(401)
def error_401(error):
    return render_template('errorpage.html', errorcode="401",
                           message="Login brah. Unauthorised."), 401


@app.errorhandler(405)
def error_405(error):
    return render_template(
        'errorpage.html', errorcode="405",
        message="What are you even trying to do? Wrong method"), 405


@app.errorhandler(500)
def error_500(error):
    return render_template(
        'errorpage.html', errorcode="500",
        message="Error (sorry, contact the site admins for more info)"), 500


def main():
    if(app.config.get('PORT')):
        app.run(host='0.0.0.0', port=app.config.get('PORT'))
    else:
        app.run(host='0.0.0.0')


def init_db():
    with app.app_context():
        db.create_all(app=app)

if __name__ == '__main__':
    main()
