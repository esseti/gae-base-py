import httplib

__author__ = 'stefano'


# always extend this class, it's used in the handler to handle the notifications
class GCAPIException(Exception):
    pass


# use this for server errors
class GCServerException(Exception):
    pass


class BadRequest(GCAPIException):
    code = 400


class BadParameters(GCAPIException):
    code = httplib.BAD_REQUEST
    __ERROR_MISSING = "Bad parameters: %s "

    def __init__(self, field):
        Exception.__init__(self)
        self.args = (self.__ERROR_MISSING % field,)


class NotFoundException(GCAPIException):
    code = httplib.NOT_FOUND
    __ERROR_MISSING = "Not found"

    def __init__(self):
        Exception.__init__(self)
        self.args = (self.__ERROR_MISSING,)


class ValidationError(GCAPIException):
    code = httplib.BAD_REQUEST
    __ERROR_MISSING = "Validation failed on field  '%s'"

    def __init__(self, field):
        Exception.__init__(self)
        self.args = ((self.__ERROR_MISSING % field),)
        self.field = field


class MissingParameters(GCAPIException):
    code = httplib.BAD_REQUEST
    __ERROR_MISSING = "The field '%s' is missing"

    def __init__(self, field):
        Exception.__init__(self)
        self.args = ((self.__ERROR_MISSING % field),)


class AuthenticationError(GCAPIException):
    code = httplib.UNAUTHORIZED

    def __init__(self, message=None):
        if message:
            self.args = ("Authentication Error: " + message,)
        else:
            self.args = ("Authentication Error",)


class ServerError(GCServerException):
    code = 500

    def __init__(self, message=None):
        if message:
            self.args = ("Server Error: " + message,)
        else:
            self.args = ("Server Error",)