""" Fabric task for MySQL. Have in note that this is Debian specific."""
from fabric.api import local, run, sudo, env, prompt
from fabric.context_managers import settings, hide
from fabric.contrib.files import exists
from fabric.utils import warn

from db import DBTypeBase, DB_CREDENTIALS_INFO_MESSAGE
from utils import generate_password, add_os_package


MYSQL_EXECUTABLE_PATH = '/usr/bin/mysql'

# On debian based systems this file contains system user and password for mysql
MYSQL_DEFAULTS_CONF = '/etc/mysql/debian.cnf'
MYSQL_RUN_COMMAND = '%s --defaults-file=%s' % (MYSQL_EXECUTABLE_PATH,
                                               MYSQL_DEFAULTS_CONF)

CREATE_DB_QUERY = """echo 'create database %s default character set utf8 collate utf8_general_ci'"""
CREATE_USER_QUERY = """echo 'grant all privileges on %s.* to %s@localhost identified by "%s"'"""


class DBType(DBTypeBase):
    def is_db_installed(self):
        if exists(MYSQL_EXECUTABLE_PATH):
            return True
        return False

    def create_db(self, name):
        """ Creates database with given name """
        sudo('%s | %s' % (CREATE_DB_QUERY, MYSQL_RUN_COMMAND) % name)
    
    def create_db_and_user(self, name):
        """ Creates database and user with the same name """
        self.create_db(name)
        self.create_user_for_db(name, name)


def setup_db_server():
    with settings(hide('warnings', 'stderr'), warn_only=True):
        result = sudo('dpkg-query --show mysql-server')
    if result.failed is False:
        warn('MySQL is already installed')
        return

    password = generate_password()

    sudo('debconf-set-selections <<< "mysql-server-5.5 mysql-server/root_password password %s"' % password)
    sudo('debconf-set-selections <<< "mysql-server-5.5 mysql-server/root_password_again password %s"' % password)
   
    add_os_package('mysql-server')
    local('touch passwords')
    db_setup_info = ("""Database Root Password\n"""
                     """Host: %s \n"""
                     """Password: %s \n""") % (env.host_string, password)
    local('echo "%s" >> passwords' % db_setup_info)


def create_user_for_db(username, dbname):
    """ Creates user with given name and grans them full permission on specified base """
    password = generate_password()
    sudo('%s | %s' % (CREATE_USER_QUERY, MYSQL_RUN_COMMAND) %
                     (dbname, username, password))
    
    db_info = DB_CREDENTIALS_INFO_MESSAGE % (env.host_string, username, dbname, password)
    local('touch passwords')
    local('echo "%s" >> passwords' % db_info)


