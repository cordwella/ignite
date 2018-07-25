# What is Ignite?

Ignite is a QR code based scavanger hunt game, built by Amelia Cordwell and Lana Cleverley during our time as
Wellington East Girls College technology prefects.

Game play is simple, we placed a bunch of QR codes (generated from the site) around the school which students can scan. (Most of these QR codes were only worth one point however this can be set from the database and double points are awarded when the marker house and the user house are the same) This act adds points to their account, and also to their (school) house (they have to provide this information when they sign up).

The Facebook page that we updated during the week we ran ignite can be found [here](https://www.facebook.com/wegcignite/), and our announcement video can be found [here](https://www.youtube.com/watch?v=64Wh9KMe0Eg&feature=youtu.be)

This version has been updated with extra administrative features, and a number of other improvements over the original one used the first year at WEGC .

![WEGC IGNITE Screenshot](https://cloud.githubusercontent.com/assets/10441829/20208092/974e8d2e-a850-11e6-9218-e3b2ade544de.png)

## Python Libraries
Ignite is built for Python 3.
Ignite uses the [Flask](http://flask.pocoo.org/) web framework, uses Sqlalchemy to access databases (typically using sqlite) as well as the pyqrcode, hashids, flask-admin, and bycrypt python libraries.

Ignite can be started by running 'ignite-run' from the directory in which it is saved.

However, it is advisable that when running Ignite as an event that an external server is used rather than the default one that flask is shipped with. (See installation below for details on setting up a webserver with it.)

## License
The code for Ignite is released under the MIT Open Source License.
The images in the static/images directory are (c) Lana Cleverley and used with permission for running IGNITE only.  (You can use them in your event but not if you are running something else.)

[Bootstrap](http://getbootstrap.com) is used here under the terms of the MIT license.
[jQuery](https://jquery.org) is used here under the terms of the MIT license.
The [Grayscale theme](http://startbootstrap.com/template-overviews/grayscale/) for bootstrap is also used under the MIT License.

## Installation

Feel free to run Ignite for your school, or any other organisation.

There are two ways to install IGNITE, as a test server for if you just want to try it out or make modifications, or there is an included bash script to install it on a webserver with Apache.

Do note however that Ignite has only been tested on Ubuntu, and any instructions to install a piece of software in the form 'apt-get' will only work on either Ubuntu or another debian based linux distro, however the rest of the commands should work in any OS that uses bash (eg Mac).

### Install for running as an event
Ignite is a flask application that can be run on any server with mod_wsgi. The basic_deploy.sh script is aimed at students who have not learned to setup a server and just want to run Ignite for their school. It sets up Ignite with mod_wsgi on the Apache webserver with Sqlite for a database.

On a fairly clean Ubuntu install (this has been tested on 14.04 but should work for most versions), clone this repo into a folder of your choice (or copy your edited version), and edit the variables at the top of the basic_deploy.sh script to match your setup.

```
git clone https://github.com/cordwella/ignite.git
cd ignite
vim basic_deploy.sh
```

Ensure that the basic_deploy.sh script is able to be executed, and as root execute it.
```
chmod +x basic_deploy.sh
sudo ./basic_deploy.sh
```

This should install and setup everything you need to get Ignite running on a proper webserver.
If you are having issues ensure Apache has all of the right file permissions.

If you have run these commands you should not need to run anymore commands, and should at this point check to see if the server is working by accessing the url in your web browser, or by using curl.

### Install for development or testing
First clone this repo into a folder of your choice:
(All of these instructions are to be followed in a terminal window on the installation computer).

```
cd /folder/of/your/choice
git clone https://github.com/cordwella/ignite.git
cd ignite/ignite
```

Make sure the permissions in this folder will allow the python program to read and write files.

Then install the necessary python libraries (or install python first if necessary). The list of the libraries are inside requirements.txt

If you want to you can use a [virtual environment](https://realpython.com/blog/python/python-virtual-environments-a-primer/). PyVenv is used here as IGNITE has only been tested running under python3.

```
pyvenv venv
source venv/bin/activate
```

Installing the libaries using pip.
```
pip install -r requirements.txt
```

You may run into a few issues of missing .h files when installing these libraries. This can be fixed by installing the packages python-dev and libffi-dev.

```
sudo apt-get python-dev
sudo apt-get libffi-dev
```

The next step is installing and setting up the database. Ignite uses SQLalchemy for database access, so it will work with most databases. If you are installing this as a development server I would recommend sqlite.

Then you must setup a configuration file - 'application.cfg', in the same directory as the ignite.py files.

It should contain these variables:
```
SECRET_KEY = secret key for session data etc
HASHID_KEY = key for the hashids which are used to generate the qrcode
ADMIN_UNAME = admin panel username
ADMIN_PWORD = admin panel password
EMAIL_USER = Gmail email username (for sending emails outwards)
EMAIL_PASS = email password
FROM_EMAIL = the email that will show up as the from email

SQLALCHEMY_DATABASE_URI = "sqlite:///db.sqlite3"

DEBUG = True if this is a test server
TEST_EMAIL = Your email if you are wanting to test emails
PORT = Optional addition port number that the server will run on (Flask defaults to 5000)
```

PLEASE NOTE: The config file is a python file so strings need to be in quote marks. More information about config files are available [here](http://flask.pocoo.org/docs/0.11/config/).

Install the Ignite helper commands with 'python3 setup.py install' (or if you are intending to make changes to the html or python code 'python3 setup.py develop').

To setup the tables in the database run 'ignite-db-setup'.

(If you are not using sqlite you will need to setup a database before running these commands.)

To start ignite on the flask development server run 'ignite-run'. This will start the server on the port specified in your config, and can be accessed at localhost or your server's IP address.

## Admin Panel

There is an admin panel built in to help with generating data. This is accesssable at /adminlogin. The passwords are the passwords specified in the config,

The admin panel has options to do all of the general CRUD operations on the database, including image uploads for the house pages.

A few things to note:
- The house color is a hex code without the hash in front. E.g. ff0000, not #ff0000 or 'Red'
- Changing a user's password here will not work as the passwords are hashed, if you want a password to be changed send a forgot password email.
- There are mass editing options for markers, one of these is to set all to inactive (or active). This means they cannot be scanned, this is very useful at the start and at the end of your IGNITE event.
- When adding static pages from the database try to keep the route to all lowercase letters.
- You can put HTML in the content area, by default the code will wrap your text to the center of the page however if you do not want this simply tick the 'no wrap' box, if you want a completely blank page that your html goes to tick custom layout.

Running from \_\_init.py\_\_ and using Flask's inbuilt web server is okay for testing however I would advise when you are running it as a big event that you use a proper webserver. You can find some tutorials about that [here](http://terokarvinen.com/2016/deploy-flask-python3-on-apache2-ubuntu) and [here](https://medium.com/@apatefraus/how-to-deploy-flask-on-ubuntu-with-python-3-and-nginx-fa48394deb7b#.izqpg59gh). There are lots of similar tutorials around but a number of them will be for python 2 so do be aware of this.

Another useful piece of information would be the [flask docs](http://flask.pocoo.org/docs/), if you are having issues or want to extend IGNITE further.

#### A note on sending emails
I have set up the email sending function to be handeled by Gmail's SMTP server, as I did not have access to my own one. If you wish to use a different one you just need to change the server in the send_email function in \_\_init.py\_\_, also you will need to change the settings
