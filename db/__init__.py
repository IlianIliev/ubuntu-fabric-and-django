from fabric.api import prompt


AVAILABLE_DB_MODULES = [
    'MySQL',
    'PostgreSQL',
]

DB_CREDENTIALS_INFO_MESSAGE = ("""Database credentials\n"""
    """Host: %s \n"""
    """DB name: %s \n"""
    """User: %s \n"""
    """Password: %s \n""")



class DBEngine(object):
    def create_user():
        raise NotImplemented

    def create_db():
        raise NotImplemented


def select_db_engine():
    text = ['Select database type. Available options:']
    [text.append('%s.%s' % pair) for pair in enumerate(AVAILABLE_DB_MODULES, 1)]
    text.append('Please enter your choice:')
    val = r'^(%s)$' %  '|'.join([str(pair[0]) for pair in enumerate(AVAILABLE_DB_MODULES, 1)])
    db_type = int(prompt('\n'.join(text), validate=val, default='1'))
    print AVAILABLE_DB_MODULES[db_type-1]
    #db_package = __import__('db.%s' % db_package_name, fromlist=['create_db_and_user'])
    #db_package.create_db_and_user(name)

