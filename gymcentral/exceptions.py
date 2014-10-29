__author__ = 'stefano'


# always extend this class, it's used in the handler to handle the notifications
class GCException(Exception):
    pass


class MissingParameters(GCException):
    code = 400
    __ERROR_MISSING = "The field %s is missing in your request"

    def __init__(self, field, code):
        self.message = (self.__ERROR_MISSING % field)
        self.code = code


class DecodingParameter(GCException):
    code = 400
    __ERROR_MISSING = "The field %s is missing in the model"

    def __init__(self, field, code):
        self.message = (self.__ERROR_MISSING % field)
        self.code = code


class AuthenticationError(GCException):
    code = 400

    def __init__(self):
        self.message = "Authentication Error"


class UserExists(GCException):
    code = 400

    def __init__(self):
        self.message = "User Already Exists"
