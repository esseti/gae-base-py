__author__ = 'stefano'


# always extend this class, it's used in the handler to handle the notifications
class GCException(Exception):
    pass


class BadRequest(GCException):
    code = 400


class MissingParameters(GCException):
    __ERROR_MISSING = "The field %s is missing in your request"

    def __init__(self, field):
        Exception.__init__(self)
        self.args = ((self.__ERROR_MISSING % field),)


class AuthenticationError(GCException):
    code = 401

    def __init__(self, message=None):
        if message:
            self.args = ("Authentication Error: "+message,)
        else:
            self.args = ("Authentication Error",)

