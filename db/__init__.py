import sys

from fabric.api import prompt, local, sudo
from fabric.contrib.files import exists

AVAILABLE_DB_MODULES = [
    ('Skip DB setup', None),
    ('MySQL', 'db.mysql.DBType'),
    ('PostgreSQL', 'db.postgresql.DBType'),
]


class DBTypeBase(object):
    def check_installation(self):
        raise NotImplementedError

    def create_user(self, *args, **kwargs):
        raise NotImplementedError

    def create_db(self, *args, **kwargs):
        raise NotImplementedError

    def create_db_and_user(self, *args, **kwargs):
        raise NotImplementedError

    def grant_privileges(self, *args, **kwargs):
        raise NotImplementedError

    def is_db_installed(self):
        if exists(self.executable_path):
            return True
        return False


def import_module(name):
    package_name, class_name = name.rsplit('.', 1)
    __import__(package_name)
    package = sys.modules[package_name]
    return getattr(package, class_name)



def select_db_type():
    text = ['Select database type. Available options:']
    [text.append('%s.%s' % (pair[0], pair[1][0])) for pair in enumerate(AVAILABLE_DB_MODULES, 1)]
    text.append('Please enter your choice:')
    val = r'^(%s)$' %  '|'.join([str(pair[0]) for pair in enumerate(AVAILABLE_DB_MODULES, 1)])
    db_type_input = int(prompt('\n'.join(text), validate=val, default='1'))
    db_type = AVAILABLE_DB_MODULES[db_type_input-1][1]
    if not db_type:
        return None
    return import_module(db_type)