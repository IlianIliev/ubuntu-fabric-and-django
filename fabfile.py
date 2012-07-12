import re, sys, os, inspect

from fabric.api import local, run, sudo, prompt
from fabric.context_managers import lcd, prefix, settings

from db import select_db_type
#from db.mysql import setup_db_server, create_db_and_user

from utils import generate_password, add_os_package


FABFILE_LOCATION = os.path.dirname(inspect.getfile(inspect.currentframe()))


# The name of the directory where the version controlled source will reside
SOURCE_DIRECTORY_NAME = 'src'


# System packages required for basic server setup
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


# Django database configuration template
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
    """ Check whether the project name corresponds to the Django project name
    restrictions. The check is copied from the Dajngo core code. As we are
    running it before the creation of the virtual environment the check whether
    the project name matches those of existing module check is skipped """
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


def ve_activate_prefix(name):
    """ Returns the path to the virtual environment activate script """
    return os.path.join(os.getcwd(), name, 'bin', 'activate')


def create_virtual_env(name='.'):
    """ Creates virtual environment with given name """
    local('virtualenv --no-site-packages %s' % name)


def create_django_project(name, dest_path=''):
    """ Creates new Django project using a pre made template """
    local('python ./bin/django-admin.py startproject --template "%s" %s %s' % (
            os.path.join(FABFILE_LOCATION, 'project_template/'),
            name,
            dest_path))
    local('mkdir %s' % os.path.join(dest_path, os.pardir, 'media'))


def generate_django_db_config(engine='', name='', user='', password='',
                              host='', port=''):
    """ Returns database configuration template with filled values """
    return DJANGO_DB_CONF % (engine, name, user, password, host, port)


def create_nginx_files(project_name, project_path):
    """ Create nginx local configuration file for the project """
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
    """Creates new virtual environment, installs Django and creates new project
    with the specified name. Prompts the user to choose DB engine and tries
    to setup database/user with the project name and random password and
    updates local settings according to the choosen database. Also creates
    nginx conf file for local usage"""
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
            create_nginx_files(name, source_path)
            manage_py_path = os.path.join(source_path, name, 'manage.py')
            local_settings_path = os.path.join(source_path, name, name, 'settings',
                                               'local.py')
            db_type_class = select_db_type()
            if db_type_class:
                db_type = db_type_class()
                if not os.path.exists(db_type.executable_path):
                    print 'Database executable not found. Skipping DB creation part.'
                    django_db_config = generate_django_db_config(db_type.engine)
                    local('echo "%s" >> %s' % (django_db_config,
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
                    if password:
                        django_db_config = generate_django_db_config(db_type.engine,
                                                                name, name,
                                                                password)
                        local('echo "%s" >> %s' % (django_db_config,
                                                   local_settings_path))
                        grant = db_type.grant_privileges(name, name)
                        if grant:
                            local('python %s syncdb' % manage_py_path)
                        else:
                            print 'Unable to grant DB privileges'
                            exit(1)
                    else:
                        print ('Unable to complete DB/User creation.'
                               'Skipping DB settings update.')
                        local('echo "%s" >> %s' % (generate_django_db_config(db_type.engine),
                                                   local_settings_path))
            else:
                local('echo "%s" >> %s' % (generate_django_db_config(),
                                               local_settings_path))
            with settings(warn_only=True):
                result = local('python %s collectstatic' % manage_py_path)
