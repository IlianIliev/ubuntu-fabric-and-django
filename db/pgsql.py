from fabric.api import sudo, local, env

from db import DB_CREDENTIALS_INFO_MESSAGE
from utils import generate_password


PGSQL_USER = 'postgres'


def create_db(name):
    """ Creates database with given name """
    sudo('createdb %s' % name, user=PGSQL_USER)


def create_user(username):
    """ Creates user with given name and grans them full permission on specified base """
    password = generate_password()
    sudo('psql -c "create user %s with password \'%s\'"' % (username, password), user=PGSQL_USER)
    db_info = DB_CREDENTIALS_INFO_MESSAGE % (env.host_string, '', username, password)
    local('touch passwords')
    local('echo "%s" >> passwords' % db_info)


def create_db_and_user(name):
    """ Creates database and user with the same name """
    create_db(name)
    create_user(name)

