""" Fabric task for MySQL. Have in note that this is Debian specific."""
from fabric.api import local, run, sudo, env, prompt
from fabric.context_managers import settings
from fabric.utils import warn

from db import DBTypeBase
from utils import generate_password, add_os_package


MYSQL_EXECUTABLE_PATH = '/usr/bin/mysql'

# On Debian based systems this file contains system user and password for mysql
MYSQL_DEFAULTS_CONF = '/etc/mysql/debian.cnf'
MYSQL_RUN_COMMAND = '%s --defaults-file=%s' % (MYSQL_EXECUTABLE_PATH,
                                               MYSQL_DEFAULTS_CONF)

CREATE_DB_QUERY = """echo 'create database %s default character set utf8 collate utf8_general_ci'"""
CREATE_USER_QUERY = """echo 'grant all privileges on %s.* to %s@localhost identified by "%s"'"""


class DBType(DBTypeBase):
    def __init__(self, *args, **kwargs):
        self.engine = 'mysql'
        self.required_packages = ['MySQL-python']
        self.executable_path = MYSQL_EXECUTABLE_PATH

    def create_db(self, name):
        """ Creates database with given name """
        res_ex = None
        with settings(warn_only=True):
            result = sudo('%s | %s' % (CREATE_DB_QUERY, MYSQL_RUN_COMMAND) % name)
        return not result.failed

    def create_user_for_db(self, dbname, username, password=None):
        if not password:
            password = generate_password()
        with settings(warn_only=True):
            result = sudo('%s | %s' % (CREATE_USER_QUERY, MYSQL_RUN_COMMAND) %
                 (dbname, username, password))
        return False if result.failed else password

    def create_db_and_user(self, name):
        """ Creates database and user with the same name """
        if self.create_db(name):
            return self.create_user_for_db(name, name)
        else:
            return False