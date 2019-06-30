SecretSanta++
=============
Secret Santa but with the ability to specify different constraints to avoid
certain matches, e.g. to avoid people getting the same names two years in a row
or to prevent couples from getting each other's names.

I have not had the time to write a proper documentation for this but the code is
commented fairly well and I have provided sample input files to demonstrate the
format required.

Some features:
* multiple recipients per gifter
* automatically send email notifications to all participants
* exclusion, low-probability and medium-probability constraints
* specify custom email subject/message templates
* automatically convert a gift value/spending limit to multiple currencies for
  insertion into the email templates
* specify HTML-formatted emails (if you want to)

License
-------
Copyright (c) 2014-2019 Joe Jacobs

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.
