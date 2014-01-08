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
    else:
        execute_from_command_line(sys.argv)
