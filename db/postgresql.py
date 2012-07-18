from fabric.api import sudo, local, env
from fabric.context_managers import settings

from db import DBTypeBase
from utils import generate_password, add_os_package

PGSQL_USER = 'postgres'
POSTGRESQL_EXECUTABLE_PATH = '/usr/bin/psql'


class DBType(DBTypeBase):
    def __init__(self, *args, **kwargs):
        self.engine = 'postgresql_psycopg2'
        self.required_system_packages = ['libpq-dev']
        self.required_packages = ['psycopg2']
        self.executable_path = POSTGRESQL_EXECUTABLE_PATH

    def create_user(self, username):
        """ Creates user with given name and grans them full permission on specified base """
        password = generate_password()
        with settings(warn_only=True):
            result = sudo('psql -c "create user %s with password \'%s\'"' %
                          (username, password),
                          user=PGSQL_USER)
        return False if result.failed else password

    def create_db(self, name):
        """ Creates database with given name """
        with settings(warn_only=True):
            result = sudo('psql -c "CREATE DATABASE %s"' % name,
                          user=PGSQL_USER)
        return not result.failed

    def create_db_and_user(self, name):
        """ Creates database and user with the same name """
        password = self.create_user(name)
        if password:
            self.create_db(name)
        return password

    def grant_privileges(self, dbname, username):
        with settings(warn_only=True):
            result = sudo('psql -c "GRANT ALL PRIVILEGES on DATABASE %s TO %s"'
                          % (dbname, username),
                          user=PGSQL_USER)
        return not result.failed

    def install(self):
        if self.is_db_installed():
            print 'Database already installed'
            return
        add_os_package('postgresql')