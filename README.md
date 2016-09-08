# What is Ignite?

Ignite is a QR code based scavanger hunt game, built by myself and Lana Cleverley during our time as
Wellington East Girls College technology prefects.

Game play is simple, we placed a bunch of QR codes (generated from the site) around the school which students can scan. (Most of these QR codes were only worth one point however this can be set from the database and double points are awarded when the marker house and the user house are the same) This act adds points to their account, and also to their (school) house (they have to provide this information when they sign up).

The Facebook page that we updated during the week we ran ignite can be found [here](https://www.facebook.com/wegcignite/), and our announcement video can be found [here](https://www.youtube.com/watch?v=64Wh9KMe0Eg&feature=youtu.be)

This version has been updated with extra administrative features, and a number of other improvements.

## Python Libraries
Ignite uses the [Flask](http://flask.pocoo.org/) web framework, MariaDB as it's database (accessed with MySQLdb), as well as the pyqrcode, hashids, and bycrypt python libraries.

Ignite can be started by running 'python \_\_init\_\_.py' from the directory in which it is saved.

However, it is advisable that when running Ignite as an event that an external server is used rather than the default one that flask is shipped with.

## License
The original code for Ignite is released under the MIT Open Source License.
Images of house prefects in the static/images, were taken at the WEGC Athletics Day and are reproduced with permission here.
The rest of the images in the static/images directory are (c) Lana Cleverley and used with permission for this project only.

[Bootstrap](http://getbootstrap.com) is used here under the terms of the MIT license.
[jQuery](https://jquery.org) is used here under the terms of the MIT license.
The [Grayscale theme](http://startbootstrap.com/template-overviews/grayscale/) for bootstrap is also used under the MIT License.

## Installation

Feel free to run Ignite for your school, or other organisation that's why it's up here.
To run ignite, you will first need to download this repo into a directory of your choice, most of the instructions here will be for Ubuntu and while in theory this should work in almost any operating system unless you have experience with setting these sorts of things up I would advise you stay with Ubuntu or some other form of debian linux.

From there you will need to install python and the libraries specified in requirements.txt, also install the other packages, most are just used to get the various python libraries to work (or are libraires in of themselves) however mariadb-server is the database. (Mariadb is a drop in replacement for MySQL so that will work too )

Once you have mariadb installed you should set up the database for Ignite. Create a database (with a sensible name like 'ignite'), and a user with permissions for it and then run the ignite.sql script inside that database. Then populate the tables with houses and markers.

From here assuming all went well the next step is to create a configuration file, -'application.cfg'.

This includes information for logins for the database and admin panel.

It should contain these variables:
```
SECRET_KEY = secret key for session data etc
HASHID_KEY = key for the hashids
ADMIN_UNAME = admin panel username
ADMIN_PWORD = admin panel password
DB_HOST = Database host (probably localhos)
DB_NAME = Database name
DB_USER = Database username
DB_PASS = Database password
EMAIL_USER = Gmail email username (for sending emails outwards)
EMAIL_PASS = email password

DEBUG = True if this is a test server
TEST_EMAIL = Your email if you are wanting to test emails
```

At this point if you run \_\_init.py\_\_, all going well you should have a server running Ignite, and the only other thing to do would be to edit the html and css to fit your organisation's aesthetic.

#### A note on sending emails
I have set up the email sending function to be handeled by Gmail's SMTP server, as I did not have access to my own one. If you wish to use a different one you just need to change the server in the send_email function in \_\_init.py\_\_, also you will need to change the settings
