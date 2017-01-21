from threading import Thread
from functools import wraps
from flask import session, redirect, flash, abort, url_for, request


def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Must be logged in.')
            # TODO: use of nextu incl post
            return redirect(url_for('login', nextu=request.url))
        return f(*args, **kwargs)
    return decorated_function


def ad_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('ad_login'):
            flash("Must be logged in as admin for this.")
            abort(401)
            # return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
