from fabric.api import prompt, local, sudo


AVAILABLE_DB_MODULES = [
    'MySQL',
#    'PostgreSQL',
]


DB_CREDENTIALS_INFO_MESSAGE = ("""Database credentials\n"""
    """Host: %s \n"""
    """DB name: %s \n"""
    """User: %s \n"""
    """Password: %s \n""")


class DBTypeBase(object):
    
    #def __init__(self, check_instal=False): 
    #    if check_instal:
    #        self.check_installation()

    def check_installation(self):
        raise NotImplementedError

    def create_user(*args, **kwargs):
        raise NotImplementedError

    def create_db(*args, **kwargs):
        raise NotImplementedError

    def create_db_and_user(*args, **kwargs):
        raise NotImplementedError


def select_db_type():
    text = ['Select database type. Available options:']
    [text.append('%s.%s' % pair) for pair in enumerate(AVAILABLE_DB_MODULES, 1)]
    text.append('Please enter your choice:')
    val = r'^(%s)$' %  '|'.join([str(pair[0]) for pair in enumerate(AVAILABLE_DB_MODULES, 1)])
    db_type_input = int(prompt('\n'.join(text), validate=val, default='1'))
    db_type = AVAILABLE_DB_MODULES[db_type_input-1]
    db_type_class = __import__('db.%s' % db_type.lower(), fromlist=['DBType'])
    return db_type_class.DBType
