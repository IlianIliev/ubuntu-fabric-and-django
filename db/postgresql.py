from fabric.api import sudo, local, env

from db import DBTypeBase, DB_CREDENTIALS_INFO_MESSAGE
from utils import generate_password


PGSQL_USER = 'postgres'
POSTGRESQL_EXECUTABLE_PATH = '/usr/bin/psql'


class DBType(DBTypeBase):
    def __init__(self, *args, **kwargs):
        self.engine = 'postgresql_psycopg2'
        self.required_packages = ['psycopg2']
        self.executable_path = POSTGRESQL_EXECUTABLE_PATH

    def create_user(self, username):
        """ Creates user with given name and grans them full permission on specified base """
        password = generate_password()
        sudo('psql -c "create user %s with password \'%s\'"' % (username, password), user=PGSQL_USER)
        return password

    def create_db(self, name):
        """ Creates database with given name """
        sudo('createdb %s' % name, user=PGSQL_USER)

    def create_db_and_user(self, name):
        """ Creates database and user with the same name """
        return self.create_user(name)