#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prism.settings")

    from django.core.management import execute_from_command_line

    if len(sys.argv) == 1:
        execute_from_command_line(sys.argv+['runserver', '0.0.0.0:8000'])
    elif sys.argv[1] == 'flush':
        from gmail.mime import email_db
        print email_db.remove()
    else:
        execute_from_command_line(sys.argv)
