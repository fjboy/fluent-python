from fp_lib.common import log

LOG = log.getLogger(__name__)


class AuthManager(object):

    def __init__(self, password):
        self.admin_password= password

    def is_valid(self, username, password):
        if username == 'admin' and password == self.admin_password:
            return True
        return False
