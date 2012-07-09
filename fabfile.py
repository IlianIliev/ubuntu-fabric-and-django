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


DJANGO_DB_CONF = """
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.%s', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '%s',                      # Or path to database file if using sqlite3.
        'USER': '%s',                      # Not used with sqlite3.
        'PASSWORD': '%s',                  # Not used with sqlite3.
        'HOST': '%s',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '%s',                      # Set to empty string for default. Not used with sqlite3.
    }
}
"""


def check_project_name(name):
    # this check is copied from the Dajngo core code, as we are running it
    # before the creation of VE the existing module check is skipped
    if not re.search(r'^[_a-zA-Z]\w*$', name):
        # Provide a smart error message, depending on the error.
        if not re.search(r'^[_a-zA-Z]', name):
            message = ('make sure the name begins '
                       'with a letter or underscore')
        else:
            message = 'use only numbers, letters and underscores'
        return False, ("%r is not a valid project name. Please %s." %
                           (name, message))
    if os.path.exists(name):
        message = ('Project with such name already exists.')
        return False, message
    return True, ''


# Start project part
def ve_activate_prefix(name):
    return os.path.join(os.getcwd(), name, 'bin', 'activate')


def create_virtual_env(name='.'):
    local('virtualenv --no-site-packages %s' % name)


def create_django_project(name, dest_path=''):
    local('python ./bin/django-admin.py startproject --template "%s" %s %s' % (
            os.path.join(FABFILE_LOCATION, 'project_template/'),
            name,
            dest_path))
    local('mkdir %s' % os.path.join(dest_path, 'static'))
    local('mkdir %s' % os.path.join(dest_path, 'media'))


def generate_django_db_config(engine='', name='', user='', password='',
                              host='', port=''):
    return DJANGO_DB_CONF % (engine, name, user, password, host, port)


def create_nginx_files(project_name, project_path):
    with file(os.path.join(FABFILE_LOCATION, 'nginx.local.conf')
              ) as nginx_local_template:
        nginx_local_content = nginx_local_template.read()
    nginx_local_content = nginx_local_content.replace('%%%project_name%%%',
                                                      project_name).\
                                              replace('%%%project_path%%%',
                                                      project_path)
    with file(os.path.join(project_path, '%s.nginx.local.conf' % project_name),
              'w+') as project_nginx_local:
        project_nginx_local.write(nginx_local_content)


def startproject(name):
    check, message = check_project_name(name)
    if not check:
        print message
        exit(1)
    create_virtual_env(name)
    source_path = os.path.abspath(os.path.join(name, SOURCE_DIRECTORY_NAME))
    local('mkdir %s' % source_path)
    with lcd(name):
        with prefix('. %s' % ve_activate_prefix(name)):
            packages_file = os.path.join(source_path,
                                         'required_packages.txt')
            local('cp %s %s' % (os.path.join(FABFILE_LOCATION,
                                             'required_packages.txt'),
                                packages_file))
            local('pip install -r %s' % packages_file)
            project_root = os.path.join(source_path, name)
            local('mkdir %s' % project_root)
            create_django_project(name, project_root)
            #create_nginx_files(name, source_path)
            manage_py_path = os.path.join(source_path, name, 'manage.py')
            local_settings_path = os.path.join(source_path, name, name, 'settings',
                                               'local.py')
            db_type_class = select_db_type()
            db_type = db_type_class()
            if not os.path.exists(db_type.executable_path):
                print 'Database executable not found. Skipping DB creation part'
                djang_db_config = generate_django_db_config(db_type.engine)
                local('echo "%s" >> %s' % (djang_db_config,
                                           local_settings_path))
            else:
                installed_packages = file(packages_file).read()
                package_list_updated = False
                for package in db_type.required_packages:
                    if package not in installed_packages:
                        local('echo "%s" >> %s' % (package, packages_file))
                        package_list_updated = True
                if package_list_updated:
                    local('pip install -r %s' % packages_file)
                password = db_type.create_db_and_user(name)
                djang_db_config = generate_django_db_config(db_type.engine,
                                                            name, name,
                                                            password)
                local('echo "%s" >> %s' % (djang_db_config, local_settings_path))
                local('python %s syncdb' % manage_py_path)
            return
            local('python %s collectstatic' % manage_py_path)

"""
# Server setup
def setup_server():
    # install system packages
    #add_os_package(' '.join(REQUIRED_SYSTEM_PACKAGES))
    setup_db_server()


def setup_db(name):
    db_type_class = select_db_type()
    db_type = db_type_class()
    db_type.create_db_and_user(name)
    return
    text = ['Before setting up database you must select its type']
    [text.append('%s [%s]' % pair) for pair in AVAILABLE_DB_MODULES]
    text.append('Please enter your choice:')
    val = r'^(%s)$' %  '|'.join([pair[1] for pair in AVAILABLE_DB_MODULES])
    db_package_name = prompt('\n'.join(text), validate=val, default=AVAILABLE_DB_MODULES[0][1])  
    db_package = __import__('db.%s' % db_package_name, fromlist=['create_db_and_user'])
    db_package.create_db_and_user(name)


def update_project():
    # git pull origin master
    # copy server files
    # sync db
    # collect static files
    # reload nginx config
    # restart uwsgi server


def deploy(git_repo):
    # create virtual env 
    # git add origin git_repo
    update_project()
"""

def arg_test(a, b=None, c=None):
    print a, b, c

def test2():
    import sys
    print sys.real_prefix
