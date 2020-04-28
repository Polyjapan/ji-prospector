To install, make a virtualenv first, so you avoid cluttering your damn pip.
Use virtualenvwrapper so the pain is reduced.

When in your virtualenv, (python3 only) just `pip install -r requirements.txt` and it should be ok.

Then, to test the thing, just `python manage.py runserver` in the `ji_prospector` folder (only for local testing).

For prod setup, install uwsgi and do the correct stuff : https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html
Also change the right settings in `app/settings.py` (like, remove the test database settings and add the real one's settings, also do whatever's needed to enable WSGI, so your webserver can hit django). I will maybe do it correctly and separate this kind of settings so you don't have 
to change it every pull.
