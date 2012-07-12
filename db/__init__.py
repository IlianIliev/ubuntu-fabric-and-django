import sys

from fabric.api import prompt, local, sudo
from fabric.contrib.files import exists


AVAILABLE_DB_MODULES = [
    ('Skip DB setup', None),
    ('MySQL', 'db.mysql.DBType'),
    ('PostgreSQL', 'db.postgresql.DBType'),
]


class DBTypeBase(object):
    """ Base Database class. """
    # TODO: Turn it to real abstract class

    def create_user(self, *args, **kwargs):
        """ Creates database user with given name and password, if no password
        is supplied it generates random one and returns it. """
        raise NotImplementedError

    def create_db(self, *args, **kwargs):
        """ Creates database with given name. """
        raise NotImplementedError

    def create_db_and_user(self, *args, **kwargs):
        """ Calls create_db and create_user consecutively. """
        raise NotImplementedError

    def grant_privileges(self, *args, **kwargs):
        """ Grants all privileges on specified database to specified user. """
        raise NotImplementedError

    def is_db_installed(self):
        """ Checks whether the specified database server executable is found
        and return the result. This is used to be a test whether the specified
        engine is installed. """
        return exists(self.executable_path)


def import_module(name):
    """ Accepts package path and return the imported class. This is used to
    import the database classes defined in AVAILABLE_DB_MODULES."""
    package_name, class_name = name.rsplit('.', 1)
    __import__(package_name)
    package = sys.modules[package_name]
    return getattr(package, class_name)


def select_db_type():
    """ Prompts the user to choose database engine from the available modules
    and return None or the module class """
    text = ['Select database type. Available options:']
    [text.append('%s.%s' % (pair[0], pair[1][0])) for pair in enumerate(AVAILABLE_DB_MODULES, 1)]
    text.append('Please enter your choice:')
    val = r'^(%s)$' %  '|'.join([str(pair[0]) for pair in enumerate(AVAILABLE_DB_MODULES, 1)])
    db_type_input = int(prompt('\n'.join(text), validate=val, default='1'))
    db_type = AVAILABLE_DB_MODULES[db_type_input-1][1]
    if not db_type:
        return None
    return import_module(db_type)