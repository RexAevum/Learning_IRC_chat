import Util

class User:
    def __init__(self, client_socket, username='', nickname=Util.generate_random_nickname(), password='@', usertype='user', realname = '-'):
        self._client_socket = client_socket
        self._username = username
        self._nickname = nickname
        self._password = password
        self._usertype = usertype
        self._status = "Offline"
        self._realname = realname

    @property
    def socket(self):
        return self._client_socket

    @property
    def username(self):
        return self._username

    @property
    def nickname(self):
        return self._nickname

    @property
    def usertype(self):
        return self._usertype

    @property
    def password(self):
        return self._password

    @property
    def status(self):
        return self._status

    @property
    def realname(self):
        return self._realname

    @username.setter
    def username(self, new_username):
        self._username = new_username

    @nickname.setter
    def nickname(self, new_nickname):
        self._nickname = new_nickname

    @usertype.setter
    def usertype(self, new_usertype):
        self._usertype = new_usertype

    @password.setter
    def password(self, new_password):
        self._password = new_password

    @status.setter
    def status(self, new_status):
        self._status = new_status

    @realname.setter
    def realname (self, new_realname):
        self._realname = new_realname
