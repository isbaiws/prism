import unittest
import os
import sys

fdn = os.path.dirname
test_folder = fdn(os.path.abspath(__file__))
app_folder = fdn(test_folder)
project_folder = fdn(app_folder)
if __name__ == '__main__':
    sys.path.append(project_folder)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prism.settings")

test_files = filter(lambda fn: fn.lower().endswith('py') and fn != '__init__.py',
        os.listdir(test_folder))
module_names = map(lambda fn: os.path.splitext(fn)[0], test_files)
modules = map(__import__, module_names)

module_vars = globals()
for m in modules:
    # I donot wanna overwrite currently exist ones like __name__
    module_vars.update({k: v for k, v in m.__dict__.items() if k not in module_vars})

# from django_test import *
# from model_test import *
# from attachreader_test import *
# from HTMLtoText_test import *

if __name__ == '__main__':
    unittest.main()
