import re, sys, os, inspect

from fabric.api import env, local, run, sudo, prompt
from fabric.context_managers import cd, lcd, prefix, settings
from fabric.contrib.console import confirm
from fabric.contrib.files import exists

from db import select_db_type
#from db.mysql import setup_db_server, create_db_and_user

from utils import generate_password, add_os_package, create_virtual_env, add_user, replace_in_template


FABFILE_LOCATION = os.path.dirname(inspect.getfile(inspect.currentframe()))


# The name of the directory where the version controlled source will reside
SOURCE_DIRECTORY_NAME = 'src'

PRODUCTION_USER = 'ubuntu'
PRODUCTION_WORKSPACE_PATH = os.path.join(os.sep, 'home', PRODUCTION_USER)

SETTINGS_TYPES = ['development', 'production']


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
    'libxml2-dev',
    #'ia32-libs', # this packages fixes the following uwsgi error -> ibgcc_s.so.1 must be installed for pthread_cancel to work 
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


def create_django_project(name, dest_path=''):
    """ Creates new Django project using a pre made template """
    local('python ./bin/django-admin.py startproject --template "%s" %s %s' % (
            os.path.join(FABFILE_LOCATION, 'django_template/'),
            name,
            dest_path))
    local('mkdir %s' % os.path.join(dest_path, os.pardir, 'media'))


def generate_django_db_config(engine='', name='', user='', password='',
                              host='', port=''):
    """ Returns database configuration template with filled values """
    return DJANGO_DB_CONF % (engine, name, user, password, host, port)


def create_uwsgi_files(project_name, project_path=None):
    """ Creates the uwsgi and nginx configuration files for development and
    production environment. The uwsgi script file is ment to be run using
    upstart """
    if not project_path:
        project_path = os.path.join(project_name)
    project_path = os.path.abspath(project_path)
    source_path = os.path.join(project_path, SOURCE_DIRECTORY_NAME)

    uwsgi_templates_dir = os.path.join(FABFILE_LOCATION, 'project_settings')
    # the last template in the line is only for local development purposes
    uwsgi_templates = [os.path.join(uwsgi_templates_dir, 'nginx.uwsgi.conf'),
                       os.path.join(uwsgi_templates_dir,
                                    'uwsgi.conf'),
                       os.path.join(uwsgi_templates_dir,
                                    'nginx.local.conf')]

    def _generate_files(input_files, output_path, data):
        for file_path in input_files:
            file_name = os.path.basename(file_path)
            with open(file_path) as template:
                output = replace_in_template(template.read(), data)
            output_file_name = '%s.%s.%s' % (data['project_name'],
                                             data['env_type'],
                                             file_name)
            output_file_path = os.path.join(output_path, output_file_name)
            if exists(output_file_path):
                if not confirm('File %s already exists, proceeding with this '
                               'task will overwrite it' % output_file_path):
                    continue
            with open(output_file_path, 'w+') as output_file:
                output_file.write(output)

    development_data = {'project_path': os.path.abspath(project_path),
                        'source_path': source_path,
                        'project_home': os.path.join(source_path,
                                                     project_name),
                        'env_type': 'development',
                        'project_name': project_name}
    _generate_files(uwsgi_templates, source_path, development_data)

    production_project_path = os.path.abspath(os.path.join(
                                        PRODUCTION_WORKSPACE_PATH,project_name))
    production_data = {'project_path': os.path.abspath(production_project_path),
                       'source_path': os.path.join(production_project_path,
                                                   SOURCE_DIRECTORY_NAME),
                       'project_home': os.path.join(production_project_path,
                                                    SOURCE_DIRECTORY_NAME,
                                                    project_name),
                       'env_type': 'production',
                       'project_name': project_name}
    _generate_files(uwsgi_templates[:-1], source_path, production_data)


def init_git_repository(source_path):
    """ Goes to the source path and initiales GIT repository there """
    with lcd(os.path.abspath(source_path)):
        local('git init')
        local('cp %s %s' % (os.path.join(FABFILE_LOCATION,
                                             'project_settings',
                                             'gitignore_base'),
                            os.path.join(source_path, '.gitignore')))


def startproject(name):
    """Creates new virtual environment, installs Django and creates new project
    with the specified name. Prompts the user to choose DB engine and tries
    to setup database/user with the project name and random password and
    updates local settings according to the choosen database. Also creates
    nginx conf file for local usage"""
    if env['host'] not in ['127.0.0.1', 'localhost']:
        print 'This task can be executed only on localhost'
        return
    check, message = check_project_name(name)
    if not check:
        print message
        exit(1)
    create_virtual_env(name, True)
    ve_path = os.path.abspath(name)
    source_path = os.path.join(ve_path, SOURCE_DIRECTORY_NAME)
    local('mkdir %s' % source_path)
    with lcd(name):
        with prefix('. %s' % ve_activate_prefix(name)):
            packages_file = os.path.join(source_path,
                                         'required_packages.txt')
            local('cp %s %s' % (os.path.join(FABFILE_LOCATION,
                                             'project_settings',
                                             'required_packages.txt'),
                                packages_file))
            local('pip install -r %s' % packages_file)
            project_root = os.path.join(source_path, name)
            local('mkdir %s' % project_root)
            create_django_project(name, project_root)
            create_uwsgi_files(name, ve_path)
            init_git_repository(source_path)
            manage_py_path = os.path.join(source_path, name, 'manage.py')
            local_settings_path = os.path.join(source_path, name, name,
                                               'settings', 'local.py')
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


def setup_server(local=False):
    """ WARNING: under development """
    with settings(warn_only=True):
        sudo('apt-get update')
    add_os_package(' '.join(REQUIRED_SYSTEM_PACKAGES))
    server_setup_info = ['-'*80, 'Server setup for %s' % env.host]
    #if not local:
    #    password = add_user(PRODUCTION_USER, True)
    #    if password:
    #        server_setup_info.append('www user password: %s' % password)
    db_type_class = select_db_type()
    if db_type_class:
        db = db_type_class()
        db_password = db.install()
        if db_password:
            server_setup_info.append('Database Root Password: %s' % db_password)
    sudo('reboot') # FIX ME: add check for is reboot required
    print '\n'.join(server_setup_info)


def generate_local_config(name, local_settings_path):
    db_type_class = select_db_type()
    if db_type_class:
        db_type = db_type_class()
        if not os.path.exists(db_type.executable_path):
            print 'Database executable not found. Skipping DB creation part.'
            return False
        else:
            password = db_type.create_db_and_user(name)
            if password:
                django_db_config = generate_django_db_config(db_type.engine,
                                                        name, name,
                                                        password)
                run('echo "%s" >> %s' % (django_db_config,
                                           local_settings_path))
                grant = db_type.grant_privileges(name, name)
                if grant:
                    return True
                else:
                    print 'Unable to grant DB privileges'
                    return False
            else:
                print ('Unable to complete DB/User creation.'
                       'Skipping DB settings update.')
                return False


def deploy_project(name, repo):
    create_virtual_env(name)
    with cd(name):
        env['cwd']
        exit()
        run('mkdir %s' % SOURCE_DIRECTORY_NAME)
        with cd(SOURCE_DIRECTORY_NAME):
            run('git clone %s .' % repo)
            with prefix('. ../bin/activate'):
                run('pip install -r required_packages.txt')
            source_path = run('pwd')
            nginx_uwsgi_conf_name = '%s.production.nginx.uwsgi' % name
            uwsgi_conf_name = '%s.production.uwsgi' % name
            with settings(warn_only=True):
                sudo('ln -s %s.conf /etc/nginx/sites-enabled/' % os.path.join(source_path,
                                                                         nginx_uwsgi_conf_name))
                sudo('ln -s %s.conf /etc/init/' % os.path.join(source_path,
                                                           uwsgi_conf_name))
            local_settings_path = os.path.join(source_path, name, name,
                                               'settings', 'local.py')
            if generate_local_config(name, local_settings_path):
                activate_prefix = os.path.join('/', 'home', SERVER_USER, 'bin', 'activate')
                with prefix(activate_prefix):
                    run('python manage')
                # syncdb
                # migrate
                sudo('initctl reload-configuration')
                sudo('initctl start %s' % uwsgi_conf_name)
                sudo('/etc/init.d/nginx restart')