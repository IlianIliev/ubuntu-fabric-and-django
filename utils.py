import string
import random

from fabric.api import sudo


def add_os_package(name):
    sudo('sudo apt-get -y install %s' % name)


def add_user(user):
    local('touch passwords')
    sudo('useradd -m %s' % (user))
    sudo('echo "%s ALL=(ALL) ALL" >> /etc/sudoers' % user)
    password = generate_password()
    sudo('echo "%s:%s" | chpasswd' % (user, password))
    local('echo "%s:%s" >> passwords' % (user, password))


def generate_password(length=10):
    """ Generates password using ASCII letters and punctuations chars """
    chars = string.ascii_letters + string.digits
    password = ''.join(random.choice(chars) for x in range(length))
    return password

