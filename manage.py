#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prism.settings")

    from django.core.management import execute_from_command_line

    if len(sys.argv) == 1:
        execute_from_command_line(sys.argv+['runserver', '0.0.0.0:8000'])
    elif sys.argv[1] == 'flush':
        # Need to init connection
        import prism.settings
        from mongoengine.connection import get_connection
        get_connection().drop_database('prism')
    elif sys.argv[1] == 'sendmail':
        import requests
        login_url = 'http://localhost:8000/login'
        post_email_url = 'http://localhost:8000/email'
        payload = {
            'username': 'test',
            'password': 'test',
        }

        def pretty_header(r):
            print '\n'.join('< %s: %s' % (k, v) for k, v in r.request.headers.items())
            print
            print '\n'.join('> %s: %s' % (k, v) for k, v in r.headers.items())
            print

        s = requests.Session()
        r = s.post(login_url, data=payload, allow_redirects=False)
        # pretty_header(r)
        if r.status_code != 302:
            print 'Login failed!!'
            sys.exit(1)

        if len(sys.argv) < 3:
            print 'Specify a file path!!'
            sys.exit(1)
        fn = sys.argv[2]
        # files = {'file': open(fn, 'rb')}
        r = s.post(post_email_url, data=open(fn, 'rb'))
        # pretty_header(r)
        # print r.json()
        print r.text
    else:
        execute_from_command_line(sys.argv)
