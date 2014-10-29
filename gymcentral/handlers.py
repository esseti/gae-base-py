import json
import logging
from gymcentral.exceptions import GCException, AuthenticationError
from webapp2 import RequestHandler
from models import User

__author__ = 'stefano'




class BaseJsonHandler(RequestHandler):
    def handle_exception(self, exception, debug_mode):
        # this can be refined for each exception
        if isinstance(exception, GCException):
            logging.debug("a GCException")
            self.response.set_status(exception.code)
            result = {
                'status_code': exception.code,
                'error_message': exception.message,
            }
            self.response.write(json.dumps(result))
        else:
            logging.debug("not a GCException")
            super(BaseJsonHandler, self).handle_exception(exception, debug_mode)

    def dispatch(self):
        self.response.headers['Content-Type'] = 'application/json'
        super(BaseJsonHandler,self).dispatch()

    def write_a_json(self, json_string):
        self.response.write(json.dumps(json_string))



class BaseJsonAuthHandler(BaseJsonHandler):

    def dispatch(self):
        auth = self.request.headers.get('Authorization')
        if 'Token' in auth:
            token = auth.split(' ')[1]
            user = User.query(User.token == token).get()
            if user:
                self.request.user = user
                super(BaseJsonAuthHandler,self).dispatch()
            else:
                raise AuthenticationError()
        else:
            raise AuthenticationError()