# -*- coding: utf-8 -*-
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

import re
import smtplib


class Emailer(object):
    _html_constructor = None
    _msg_constructor = None
    _sub_constructor = None
    _sender_email = None
    _sender_name = None
    _email_regex = None
    _reply_email = None
    _smtp = None

    def __init__(
        self,
        smtp_host,
        smtp_port,
        smtp_username,
        smtp_password,
        sender_email,
        sender_name,
        reply_email,
        sub_constructor,
        msg_constructor,
        html_constructor,
    ):
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
        self._sender_name = sender_name
        self._reply_email = reply_email

        # launch smtp connection
        self._smtp = smtplib.SMTP(smtp_host, smtp_port)
        self._smtp.starttls()
        self._smtp.login(smtp_username, smtp_password)

    def __del__(self):
        # close smtp connection
        self._smtp.quit()

    def send(self, gifter_name, gifter_email, recipients):
        # validate gifter email address
        assert self._email_regex.match(gifter_email)

        # construct the subject, message and email addresses
        sub = self._sub_constructor.construct(gifter_name, recipients)
        msg = self._msg_constructor.construct(gifter_name, recipients)
        reply_addr = f"{self._sender_name} <{self._reply_email}>"
        from_addr = f"{self._sender_name} <{self._sender_email}>"
        to_addr = f"{gifter_name} <{gifter_email}>"

        # construct the email
        email = None

        # only add HTML if necessary
        if self._html_constructor:
            email = MIMEMultipart("alternative")
            html = self._html_constructor.construct(gifter_name, recipients)
            email.attach(MIMEText(msg, "plain"))
            email.attach(MIMEText(html, "html"))
        else:
            email = MIMEText(msg)

        email["Date"] = formatdate(localtime=True)
        email["Reply-To"] = reply_addr
        email["From"] = from_addr
        email["Subject"] = sub
        email["To"] = to_addr

        # send the email
        self._smtp.send_message(email, from_addr=from_addr, to_addrs=[to_addr])
