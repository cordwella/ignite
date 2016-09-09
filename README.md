# What is Ignite?

Ignite is a QR code based scavanger hunt game, built by myself and Lana Cleverley during our time as
Wellington East Girls College technology prefects.

Game play is simple, we placed a bunch of QR codes (generated from the site) around the school which students can scan. (Most of these QR codes were only worth one point however this can be set from the database and double points are awarded when the marker house and the user house are the same) This act adds points to their account, and also to their (school) house (they have to provide this information when they sign up).

The Facebook page that we updated during the week we ran ignite can be found [here](https://www.facebook.com/wegcignite/), and our announcement video can be found [here](https://www.youtube.com/watch?v=64Wh9KMe0Eg&feature=youtu.be)

This version has been updated with extra administrative features, and a number of other improvements over the original one used the first year at WEGC .

## Python Libraries
Ignite is built for Python 3.
Ignite uses the [Flask](http://flask.pocoo.org/) web framework, MariaDB as it's database (accessed with PyMySQL), as well as the pyqrcode, hashids, and bycrypt python libraries.

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

Feel free to run Ignite for your school, or any other organisation.

Do note however that Ignite has only been tested on Ubuntu.

First clone this repo into a folder of your choice:
(All of these instructions are to be followed in a terminal window on the installation computer)

```
cd /folder/of/your/choice
git clone https://github.com/cordwella/eli-dmx.git
```

Make sure the permissions in this folder will allow the python program to read and write files.

Then install the necessary python libraries (or install python first if necessary). The list of the libraries are inside requirements.txt

If you want to you can use a [virtual environment](https://realpython.com/blog/python/python-virtual-environments-a-primer/).

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

The next step is installing and setting up the database. You can use either MySQL or it's drop in replacement Mariadb.

```
sudo apt-get install mariadb-server
```

Then set up a database for ignite and inside run `source ignite.sql`. This file will set up all of the database tables. (You can access mariadb by running `mysql <databasename> -u <username> -p`).

From here assuming all went well the next step is to create a configuration file, -'application.cfg'.

This includes information for logins for the database and admin panel.

It should contain these variables:
```
SECRET_KEY = secret key for session data etc
HASHID_KEY = key for the hashids which are used to generate the qrcode
ADMIN_UNAME = admin panel username
ADMIN_PWORD = admin panel password
DB_HOST = Database host (probably localhost)
DB_NAME = Database name
DB_USER = Database username
DB_PASS = Database password
EMAIL_USER = Gmail email username (for sending emails outwards)
EMAIL_PASS = email password

DEBUG = True if this is a test server
TEST_EMAIL = Your email if you are wanting to test emails
PORT = Optional addition port number that the server will run on (Flask defaults to 5000)
```

At this point if you run \_\_init.py\_\_, all going well you should have a server running Ignite (Flask will spit out the ip and port address in the terminal). Test it out to make sure you don't get any errors. However it will have no data about houses or markers. Currently the only way to add houses or markers is to do it directly in the database with SQL statements, but an admin panel is in the works.

E.G.
```sql
-- Insert a house into the house table
INSERT INTO `houses` (name, desc, shortdesc, captain, color) VALUES ('Bledisloe','Bledisloe house has won the athletics day competition for the last four years in a row, and the overall house cup for the last three - these stats alone show you that Bledisloe house is not one to mess with!','Red Hot and can\'t be stopped','Ellie Shea','ff0000');

-- Insert a marker into the marker table
INSERT INTO `markers` (name, house_id, point_value) VALUES ('Red head',1,1),('TOO HOT',1,2),('HOT DAMN',1,1),('Let all the colours ignite tonight',1,1);
```

Running from \_\_init.py\_\_ and using Flask's inbuilt web server is okay however I would advise when you are running it as a big event that you use a proper webserver. You can find some tutorials about that [here](http://terokarvinen.com/2016/deploy-flask-python3-on-apache2-ubuntu) and [here](https://medium.com/@apatefraus/how-to-deploy-flask-on-ubuntu-with-python-3-and-nginx-fa48394deb7b#.izqpg59gh). There are lots of simular tutorials around but a number of them will be for python 2 so do be aware of this.

You can access the current admin panel by going to {host and port number}/admin/login, but it only has the option to generate the zip file of QR codes and/or download it.

#### A note on sending emails
I have set up the email sending function to be handeled by Gmail's SMTP server, as I did not have access to my own one. If you wish to use a different one you just need to change the server in the send_email function in \_\_init.py\_\_, also you will need to change the settings
