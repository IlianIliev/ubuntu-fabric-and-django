import re, sys, os

from fabric.api import local, run, sudo, prompt
from fabric.context_managers import lcd, prefix

from db import AVAILABLE_DB_MODULES
from db.mysql import setup_db_server, create_db_and_user

from utils import generate_password, add_os_package


DIRECTORY_NAME_REGEXP = r'^[a-zA-Z_].[\w_-]+$'

SOURCE_DIRECTORY_NAME = 'src'

REQUIRED_SYSTEM_PACKAGES = [
    'python-pip',
    'gcc',
    'python-dev',
    'libjpeg-dev',
    'libfreetype6-dev',
    'git',
    'nginx',
    'python-virtualenv',
]


def setup_server():
    # install system packages
    #add_os_package(' '.join(REQUIRED_SYSTEM_PACKAGES))
    setup_db_server()


def setup_db(name):
    text = ['Before setting up database you must select its type']
    [text.append('%s [%s]' % pair) for pair in AVAILABLE_DB_MODULES]
    text.append('Please enter your choice:')
    val = r'^(%s)$' %  '|'.join([pair[1] for pair in AVAILABLE_DB_MODULES])
    db_package_name = prompt('\n'.join(text), validate=val, default=AVAILABLE_DB_MODULES[0][1])
    db_package = __import__('db.%s' % db_package_name, fromlist=['create_db_and_user'])
    db_package.create_db_and_user(name)



"""
This fabric script automates the creation of a virtual environment and a Django
project. The result will be virtual environtment with the name of the project.
The folder namer where the project code will be placed is specified in
SOURCE_DIRECTORY_NAME, a static root folder will be created and settings.py
will be updated.
"""


def create_virtual_env():
    local('virtualenv --no-site-packages .')


def create_project_directory(name):
    if name is None:
	print 'You should provide project name to use this script'
        sys.exit()
    if not re.match(DIRECTORY_NAME_REGEXP, name):
        print 'Incorrect name, name can contain only numbers, letters, dash ' \
            'and underscore and should start with letter or underscore'
        exit(1)
    else:
        local('mkdir %s' % name)


def install_packages():
    local('pip install -r required_packages.txt')


def create_django_project(name):
    local('mkdir %s' % SOURCE_DIRECTORY_NAME)
    local('mkdir static')
    local('mkdir media')
    local('python ./bin/django-admin.py startproject --template "./project_template/" %s %s' % (name, SOURCE_DIRECTORY_NAME))


def start_project(name=None):
    import inspect, os
    print os.path.dirname(inspect.getfile(inspect.currentframe()))
    exit()

    create_project_directory(name)
    local('cp required_packages.txt %s' % name)
    with lcd(name):
        create_virtual_env()
        ve_activate_prefix = os.path.join(os.getcwd(), name, 'bin', 'activate')
        with prefix('. %s' % ve_activate_prefix):
            install_packages()
            create_django_project(name)
            create_db_and_user()
            manage_py_path = os.path.join(SOURCE_DIRECTORY_NAME, 'manage.py')
            local('python %s collectstatic' % manage_py_path)
