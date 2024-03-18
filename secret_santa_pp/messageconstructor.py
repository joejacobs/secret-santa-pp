# flake8: noqa
from datetime import date

import currency


# return the number of days to christmas
def _days_to_christmas():
    today = date.today()
    christmas = date(date.today().year, 12, 25)
    return str((christmas - today).days)


# replace occurrences of old with new n times starting from the back
def _rev_replace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


class MessageConstructor(object):
    _msg = None

    def __init__(
        self, msg, limit_value=None, limit_currency=None, display_currencies=[]
    ):
        # message cannot be blank
        assert msg
        assert len(msg.strip())

        # replace curly bracket placeholders with values
        self._msg = msg.replace("{days_to_christmas}", _days_to_christmas())
        self._msg = self._msg.replace("{year}", str(date.today().year))

        # stop here if spending limit or limit tag isn't specified
        if not limit_value or limit_value == 0 or "{limit}" not in msg:
            assert "{limit}" not in msg
            return

        # ensure limit tag, limit currency and display currencies are specified
        assert limit_value > 0
        assert limit_currency
        assert display_currencies

        limits = []

        for c in display_currencies:
            val = limit_value

            if c != limit_currency:
                # convert value from limit currency to display currency
                val = round(currency.convert(limit_currency, c, limit_value))

            limits.append(currency.pretty(val, c))

            # hack to replace $ with US$ for USD
            if c == "USD" and limits[-1][:3] != "US$":
                limits[-1] = "US{}".format(limits[-1])

        # replace limit placeholder in message and store it
        self._msg = self._msg.replace("{limit}", "/".join(limits))

    # construct a message, inserting gifter and recipient names
    def construct(self, gifter_name, recipient_names):
        recipients_str = ", ".join(recipient_names)
        recipients_str = _rev_replace(recipients_str, ",", " and", 1)
        msg = self._msg.replace("{gifter}", gifter_name)
        return msg.replace("{recipients}", recipients_str)
