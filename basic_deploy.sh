#!/bin/bash

# MODIFY THESE VAIRABLES FOR YOUR SETUP
SECRET_KEY= # Random secret key for encrypting cookies
HASHID_HEY= # Key for encrypting/decrypting QR code urls
            # This will need to be the same in the place you have created
			# and are accessing the QR codes from, just coping over the db
			# isn't enough
DB_FILE_NAME=file.db # Name of a file to create and save data in (sqlilte file)
EMAIL_USER= # Gmail Email Address to send emails through
EMAIL_PASS= # Gmail password to send emails through

ADMIN_UNAME= # Username for /adminlogin
ADMIN_PWORD= # Password for /adminlogin

DEBUG=False # True or False (watch the capitals)
TEST_EMAIL= # An email address you want all emails to be sent to if DEBUG=True


# I am assuming that you are running this from the directory
# the ignite source code resides in, if not overwrite this variable
# with where it is (top level directory with README.md and requirements.txt)
IGNITE_DIR=$(pwd)

apt update --yes -q
apt upgrade --yes -q
# Install Prerequisites for python libraries
apt install --yes -q python3-dev libffi-dev python3 curl python3-pip python-virtualenv -q

# Write the config file
mkdir /etc/ignite/
touch /etc/ignite/application.cfg

cat > /etc/ignite/application.cfg << EOF
SECRET_KEY = '$SECRET_KEY'
HASHID_KEY = 'hashkey'
ADMIN_UNAME = '$ADMIN_UNAME'
ADMIN_PWORD = '$ADMIN_PWORD'
EMAIL_USER = '$EMAIL_USER'
EMAIL_PASS = '$EMAIL_PASS'
SQLALCHEMY_DATABASE_URI = "sqlite:///$IGNITE_DIR/$DB_FILE_NAME"
PORT = 80
DEBUG = $DEBUG
TEST_EMAIL = '$TEST_EMAIL'

EOF

# Setup IGNITE python
python3 -m pip install -r requirements.txt
python3 setup.py develop
ignite-db-setup

# Setup Apache
apt install apache2 libapache2-mod-wsgi-py3 -y -q
a2enmod wsgi

# Create VirtualHost file definiing how to run the server
touch /etc/apache2/sites-available/ignite.conf
cat > /etc/apache2/sites-available/ignite.conf << EOF
<VirtualHost *:80>

		WSGIDaemonProcess ignite
		WSGIProcessGroup ignite

		WSGIScriptAlias / $IGNITE_DIR/ignite.wsgi
		<Directory $IGNITE_DIR>
			Require all granted
		</Directory>

		Alias /static $IGNITE_DIR/ignite/static
		<Directory $IGNITE_DIR/ignite/static/>
			Require all granted
		</Directory>

		ErrorLog \${APACHE_LOG_DIR}/error.log
		LogLevel warn
		CustomLog \${APACHE_LOG_DIR}/access.log combined
</VirtualHost>

EOF

# File Permissions for apache2
find $IGNITE_DIR -type d -exec chmod 771 {} +
find $IGNITE_DIR -type f -exec chmod 660 {} +

chmod o+x $IGNITE_DIR/ignite.wsgi

chmod 664 $IGNITE_DIR/$DB_FILE_NAME
chown :www-data $IGNITE_DIR -R

# Enable site and restart apache2
a2ensite ignite
a2dissite 000-default
service apache2 restart


echo "IGNITE enabled and running on port 80"
echo "The database will be stored in a file called $IGNITE_DIR/$DB_FILE_NAME"
echo "To make a backup or export of the data simply copy that file"
echo "Admin panel is available at /adminlogin"
echo "The configuration file is stored at /etc/ignite/application.cfg"
echo "To reload the server after making modifications to IGNITE, run 'sudo service apache2 restart'"
