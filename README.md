# Install + test
To install, make a virtualenv first, so you avoid cluttering your damn pip.
Use virtualenvwrapper so the pain is reduced.

When in your virtualenv, (python3 only) just `pip install -r requirements.txt` and it should be ok.

Then, to test the thing, just `python manage.py runserver` in the `ji_prospector` folder (only for local testing).

# Prod setup
Django doesn't serve itself. You gotta install uwsgi, which will serve the django app (see here https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html)
Also duplicate `app/settings_local.placeholder.py` into `app/settings_local.py` and set the right local stuff (static root = the same as configured in your nginx sites-enabled file, database = whatever you have on your server..)

Install npm dependencies with `npm ci` in the `ji_prospector` folder.

Run `python manage.py collectstatic` in the `ji_prospector` folder or else you won't have any JS or CSS.
