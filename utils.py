import string
import random

from fabric.api import local, run, sudo
from fabric.context_managers import settings


def add_os_package(name):
    sudo('sudo apt-get -y install %s' % name)


def add_user(user, make_sudoer = False):
    with settings(warn_only=True):
        result = sudo('useradd -m %s' % (user))
    if not result.failed:
        if make_sudoer:
            sudo('echo "%s ALL=(ALL) ALL" >> /etc/sudoers' % user)
        password = generate_password()
        sudo('echo "%s:%s" | chpasswd' % (user, password))
        return password
    return False


def generate_password(length=10):
    """ Generates password using ASCII letters and punctuations chars """
    chars = string.ascii_letters + string.digits
    password = ''.join(random.choice(chars) for x in range(length))
    return password


def create_virtual_env(name='.', run_locally=False):
    """ Creates virtual environment with given name """
    runner = local if run_locally else run
    runner('virtualenv --no-site-packages %s' % name)


def replace_in_template(input, data={}):
    for var in data:
        input = input.replace('%%%%%%%s%%%%%%' % var, data[var])
    return input