import re, sys, os, inspect

from fabric.api import local, run, sudo, prompt
from fabric.context_managers import lcd, prefix

from db import select_db_type
#from db.mysql import setup_db_server, create_db_and_user

from utils import generate_password, add_os_package


FABFILE_LOCATION = os.path.dirname(inspect.getfile(inspect.currentframe()))

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


# Start project part
def create_virtual_env():
    local('virtualenv --no-site-packages .')


def install_packages():
    local('pip install -r required_packages.txt')


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


def create_django_project(name):
    local('mkdir %s' % SOURCE_DIRECTORY_NAME)
    local('mkdir static')
    local('mkdir media')
    local('python ./bin/django-admin.py startproject --template "%s" %s %s' % (os.path.join(FABFILE_LOCATION, 'project_template/'), name, SOURCE_DIRECTORY_NAME))


def startproject(name=None):
    create_project_directory(name)
    
    with lcd(name):
        create_virtual_env()
        local('cp %s .' % os.path.join(FABFILE_LOCATION, 'required_packages.txt'))
        ve_activate_prefix = os.path.join(os.getcwd(), name, 'bin', 'activate')
        with prefix('. %s' % ve_activate_prefix):
            install_packages()
            create_django_project(name)
            with select_db_engine as db_engine:
                create_db_and_user(name, local=True)
            update_settings()
            copy_fabfiles()
            manage_py_path = os.path.join(SOURCE_DIRECTORY_NAME, 'manage.py')
            local('python %s collectstatic' % manage_py_path)


# Server setup
def setup_server():
    # install system packages
    #add_os_package(' '.join(REQUIRED_SYSTEM_PACKAGES))
    setup_db_server()


def setup_db(name):
    db_type_class = select_db_type()
    db_type = db_type_class(local_run=True)
    db_type.create_db_and_user(name)
    return
    text = ['Before setting up database you must select its type']
    [text.append('%s [%s]' % pair) for pair in AVAILABLE_DB_MODULES]
    text.append('Please enter your choice:')
    val = r'^(%s)$' %  '|'.join([pair[1] for pair in AVAILABLE_DB_MODULES])
    db_package_name = prompt('\n'.join(text), validate=val, default=AVAILABLE_DB_MODULES[0][1])  
    db_package = __import__('db.%s' % db_package_name, fromlist=['create_db_and_user'])
    db_package.create_db_and_user(name)

