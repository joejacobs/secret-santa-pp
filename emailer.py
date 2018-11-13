# -*- coding: utf-8 -*-
from email.message import EmailMessage
from email.utils import formatdate

import re
import smtplib


class Emailer(object):
    _html_constructor = None
    _msg_constructor = None
    _sub_constructor = None
    _sender_email = None
    _email_regex = None
    _reply_email = None
    _smtp = None

    def __init__(self, smtp_address, smtp_port, smtp_username, smtp_password,
                 sender_email, reply_email, sub_constructor, msg_constructor,
                 html_constructor):
        # validate email addresses and port number
        self._email_regex = re.compile(r"[^@]+@[^@]+\.[^@]+")
        assert self._email_regex.match(sender_email)
        assert self._email_regex.match(reply_email)
        assert smtp_port > 0

        # store for later
        self._html_constructor = html_constructor
        self._sub_constructor = sub_constructor
        self._msg_constructor = msg_constructor
        self._sender_email = sender_email
        self._reply_email = reply_email

        # launch smtp connection
        self._smtp = smtplib.SMTP(smtp_address, smtp_port)
        self._smtp.starttls()
        self._smtp.login(smtp_username, smtp_password)

    def __del__(self):
        # close smtp connection
        self._smtp.quit()

    def send(self, gifter_name, gifter_email, recipients):
        # validate gifter email address
        assert self._email_regex.match(gifter_email)

        # construct the subject and message
        sub = self._sub_constructor.construct(gifter_name, recipients)
        msg = self._msg_constructor.construct(gifter_name, recipients)

        # constructing the email
        email = EmailMessage()
        email.set_content(msg)
        email["Subject"] = sub
        email["Date"] = formatdate(localtime=True)
        email["From"] = self._sender_email
        email["To"] = gifter_email
        email["Reply-To"] = self._reply_email

        # only add HTML if necessary
        if self._html_constructor:
            html = self._html_constructor.construct(gifter_name, recipients)
            email.add_alternative(html, subtype="html")

        # send the email
        self._smtp.send_message(email)
