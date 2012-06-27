import re
from fabric.api import local, run, sudo
from utils import generate_password
MYSQL_EXECUTABLE_PATH = '/usr/bin/mysql'

# On debian based systems this file contains system user and password for mysql
MYSQL_DEFAULTS_CONF = '/etc/mysql/debian.cnf'
MYSQL_RUN_COMMAND = '%s --defaults-file=%s' % (MYSQL_EXECUTABLE_PATH,
                                               MYSQL_DEFAULTS_CONF)

CREATE_DB_QUERY = """echo 'create database %s default character set utf8 collate utf8_general_ci'"""
CREATE_USER_QUERY = """echo 'grant all privileges on %s.* to %s@localhost identified by "%s"'"""


def create_db_and_user(name):
    """ Creates database and user with the same name """
    sudo('%s | %s' % (CREATE_DB_QUERY, MYSQL_RUN_COMMAND) % name)
    password = generate_password()
    sudo('%s | %s' % (CREATE_USER_QUERY, MYSQL_RUN_COMMAND) % (name, name, password))
