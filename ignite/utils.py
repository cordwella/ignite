import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ignite.decorators import async


# TODO: this, better, less convoluted
def clean_str(s):
    # s.decode('ascii')
    # Check For html
    return s


def is_clean_username(s):
    """ Checks that it does not contain 'banned words' as defined in a file
    and is between expected lengths, and is alpha numeric
    """
    import pkg_resources
    import os
    resource_package = __name__
    resource_path = os.path.join('banned-words.csv')
    text = str(pkg_resources.resource_string(resource_package, resource_path))
    banned_words = text.splitlines()
    for word in banned_words:
        if word in s:
            return False
    return s.isalnum() and len(s) >= 5 and len(s) <= 20


def bad_password_check(s):
    if(len(clean_str(s)) >= 5):
        return clean_str(s)
    return False


def email_validate(s):
    import re
    return re.match("[^@]+@[^@]+\.[^@]+", s) and clean_str(s)


@async
def send_email(toadrr, message, subject, fromaddr=None):
    import ignite
    app = ignite.app

    if not fromaddr:
        fromaddr = app.config.get('EMAIL_USER')
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

    server.login(username, password)
    if app.config['DEBUG']:
        server.sendmail(fromaddr, app.config['TEST_EMAIL'], msg.as_string())
    else:
        server.sendmail(fromaddr, msg['To'], msg.as_string())
    server.quit()
