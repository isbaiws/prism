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

    elif sys.argv[1].startswith('api'):
        from bson import BSON, Binary
        from hashlib import md5
        from urlparse import urljoin
        import uuid
        from pprint import pprint
        import requests
        from bson.objectid import ObjectId
        from prism import settings

        def require_args(*args):
            if len(sys.argv) < len(args)+2:
                print 'Usage:', ' '.join(sys.argv[:2]), ' '.join(args)
                sys.exit(1)
            if len(args) == 1:
                return sys.argv[2]
            return sys.argv[2:len(args)+2]

        def sign():
            return md5('%s'*6 % (
                devid, version, source, action, nonce, 
                settings.API_SECRET_KEY)).hexdigest().lower()

        api_host = 'http://localhost:8000/api/'
        version = 6
        source = 22
        nonce = 1392696510

        if sys.argv[1] == 'api-login':
            u, p = require_args('username', 'password')
            devid = uuid.uuid4()
            action = 102

            pay_load = {
                    'devid': devid,
                    'ver': version,
                    'source': source,
                    'action': action,
                    'nonce': nonce,
                    'sig': sign(),
                    'username': u,
                    'password': p,
                }
            pprint(requests.post(urljoin(api_host, 'login'), BSON.encode(pay_load)).json())
        elif sys.argv[1] == 'api-init':
            devid = uuid.uuid4()
            action = 101

            pay_load = {
                    'devid': devid,
                    'ver': version,
                    'source': source,
                    'action': action,
                    'nonce': nonce,
                    'sig': sign(),
                    'uid': ObjectId(require_args('userid')),
                }
            print 'device id is', devid
            pprint(requests.post(urljoin(api_host, 'init'), BSON.encode(pay_load)).json()) 

        elif sys.argv[1] == 'api-upload':
            action = 111
            devid, folder, path = require_args('device-id', 'folder', 'path-to-email')

            pay_load = {
                    'devid': uuid.UUID(devid),
                    'ver': version,
                    'source': source,
                    'action': action,
                    'nonce': nonce,
                    'sig': sign(),
                    'data': [{
                        'id': 1,
                        'typeid': 105,
                        'data': {
                            'folder': folder,
                            'content': Binary(open(path, 'rb').read()),
                        }
                    }]
                }
            pprint(requests.post(urljoin(api_host, 'upload'), BSON.encode(pay_load)).json()) 
        else:
            print 'What are you trying to do with %s?' % sys.argv[1] 

    elif sys.argv[1] == 'createsuperuser':
        if len(sys.argv) < 4:
            print 'Usage: ./manage.py createsuperuser username password'
            sys.exit(1)
        from gmail.models import User
        username = sys.argv[2]
        password = sys.argv[3]
        if User.exist(username=username):
            print 'Username %s already exists' % username
            sys.exit(1)
        u = User.create_user(username, password, is_superuser=True)
        print 'Created', u.username
    else:
        execute_from_command_line(sys.argv)
