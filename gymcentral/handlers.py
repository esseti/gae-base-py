import logging
import datetime
import os

from google.appengine.ext import ndb
from webapp2 import RequestHandler
from webapp2_extras import json
from webapp2_extras.appengine.auth.models import User
from webapp2_extras.securecookie import SecureCookieSerializer

from gymcentral.exceptions import GCException, MissingParameters


__author__ = 'stefano'


def gcmethod(in_data=[], out_data=[]):
    def decorate(func):
        func.__out_parameters = out_data
        func.__in_parameters = in_data
        return func

    return decorate


class BaseJsonHandler(RequestHandler):
    __out_parameters = []
    __in_parameters = []
    __OUR_DOMAIN = "http://localhost"
    __SECURE = False

    def __init__(self, request, response):
        self.initialize(request, response)
        self.__SECRET_KEY = os.environ.get("SECRET_KEY")
        self.__AUTH_TYPE = os.environ.get("AUTH_TYPE")

    # TODO make these two as annotations
    def set_out_pars(self, l):
        """
        set the output parameters
        :param l:
        :return:
        """
        self.__out_parameters = l

    def set_in_pars(self, l):
        """
        set the in parameter (request) for the current method.
        It calls init_requet to get the request parameters accordingly to just specified list
        :param l:
        :return:
        """
        self.__in_parameters = l
        # recall this function to process input
        self.init_request()

    def auth_user(self, user):
        """
        creates the cookie for current user
        :param user_id:
        :param token:
        :return:
        """
        user_id = user.get_id()
        # TODO: do i've to create a new one everytime?
        user_token = User.create_auth_token(user_id)
        token = str(user_id) + "|" + user_token
        if int(self.__AUTH_TYPE) == 1:
            self.render({"token": token})
        elif int(self.__AUTH_TYPE) == 2:
            scs = SecureCookieSerializer(self.__SECRET_KEY)
            token = scs.serialize('token', token)
            expiration = datetime.datetime.now() + datetime.timedelta(minutes=1)
            self.response.set_cookie('gc_token', token, path='/', secure=self.__SECURE,
                                     expires=expiration)
            self.render()
        else:
            raise Exception("Auth type error")


    def handle_exception(self, exception, debug_mode):
        """
        Mangager of exeception
        :param exception:
        :param debug_mode:
        :return:
        """
        logging.debug("handle exception")
        # this can be refined for each exception
        if isinstance(exception, GCException):
            logging.debug("a GCException")
            self.response.set_status(exception.code)
            result = {
                'status_code': exception.code,
                'error_message': exception.message,
            }
            self.response.write(json.encode(result))
        else:
            logging.debug("not a GCException")
            super(BaseJsonHandler, self).handle_exception(exception, debug_mode)

    def dispatch(self):
        self.response.headers['Content-Type'] = 'application/json'
        # crete the request object
        self.init_request()
        super(BaseJsonHandler, self).dispatch()

    def init_request(self):
        """
        Initialize request
        :return:
        """
        obj_in = self.__deserialize_request(self.request)
        self.request.in_dict = obj_in

    def __deserialize_request(self, request):
        """
        Transform the request into a json object.
        :param request: the request object
        :param parameter: the parameters that have to be in the result
        :return: The json object
        """
        ret = {}
        list = []
        # if there's input then use that fields, otherwise everything
        if self.__in_parameters:
            lp = self.__in_parameters
        else:
            lp = request.params
        for parameter in lp:
            # logging.debug("par %s = %s " % (parameter, request.get(parameter)))
            value = request.get(parameter, default_value=None)
            logging.debug("req %s %s " % (parameter, value))
            if value:
                ret[parameter] = value
            else:
                raise MissingParameters(parameter, 404)
        return ret

    def __serialize_dict(self, in_dict):
        """
        Serialize a dictionary to a json putting only the parameters that were specified.
        :param dict:
        :return:
        """
        ret = {}
        for parameter in in_dict:

            if hasattr(in_dict[parameter], 'isoformat'):
                ret[parameter] = str(in_dict[parameter])
            else:
                ret[parameter] = in_dict[parameter]

        # then use only the out pars
        if self.__out_parameters:
            temp_ret = {}
            for parameter in self.__out_parameters:
                if parameter in ret:
                    temp_ret[parameter] = ret[parameter]
                else:
                    logging.error("Field required '%s' is not in the object", parameter)
                    # raise Exception("Field required is not in the object")
            ret = temp_ret

        return ret

    def __serialize_object(self, object):
        """
        Transform an ndb object into JSON
        :param object: an object
        :param parameters: list of parameters to put
        :return: the json
        """

        # get the dict
        o_dict = object.to_dict()
        o_dict['id'] = object.key.id()
        return self.__serialize_dict(o_dict)

    def __serialize_list(self, l_in, token=None):
        """
        Transform an list of dict to json
        :param object: a list NDB
        :param parameters: list of parameters to put
        :return: the json
        """
        ret = {}
        l = []
        for o in l_in:
            if isinstance(o, dict):
                l.append(self.__serialize_dict(o))
            elif isinstance(o, ndb.Model):
                l.append(self.__serialize_object(o))
        ret['objects'] = l
        if token:
            ret['nextPage'] = token
        return ret

    def __render_dict_to_json(self, in_dict):
        """
        Renders a dictionary in a json
        :param in_dict:
        :return:
        """
        self.response.write(json.encode(self.__serialize_dict(in_dict)))

    def __render_list_to_json(self, in_list, token=None):
        """
        Renders a list of dict in json. If paginated renders the token
        :param in_list:
        :param token:
        :return:
        """
        self.response.write(json.encode(self.__serialize_list(in_list, token)))

    def __render_object_to_json(self, in_dict):
        """
        renders a ndb object to json
        :param in_dict:
        :return:
        """
        self.response.write(json.encode(self.__serialize_object(in_dict)))

    def render(self, o=None, **kwargs):
        # TODO: what about passing **kwargs?
        if o is None:
            self.response.set_status(200)
        elif isinstance(o, dict):
            self.__render_dict_to_json(o, **kwargs)
        elif isinstance(o, list):
            logging.debug('is a list')
            self.__render_list_to_json(o, **kwargs)
        elif isinstance(o, ndb.Model):
            self.__render_object_to_json(o, **kwargs)
        elif isinstance(o, str):
            self.response.write(o)


class BaseJsonAuthHandler(BaseJsonHandler):

    def __init__(self, request, response):
        self.initialize(request, response)
        # those two are not inherited from Base class
        self.__SECRET_KEY = os.environ.get("SECRET_KEY")
        self.__AUTH_TYPE = os.environ.get("AUTH_TYPE")


    def get_user(self):
        """
        Get the user from the authorization. Works for HttpAuth or token.
        TODO: can someone check if this is correct?
        :return: the user or None
        """
        logging.debug("%s", int(self.__AUTH_TYPE))
        if int(self.__AUTH_TYPE) == 1:
            token = self.request.headers.get("Authorization")
            if token:
                uid, ut = token.split("Token")[1].split("|")
            else:
                return None
        elif int(self.__AUTH_TYPE) == 2:
            logging.debug("here")
            scs = SecureCookieSerializer(self.__SECRET_KEY)
            token = self.request.cookies.get('gc_token')
            if token:
                uid, ut = scs.deserialize('token', token).split("|")
            else:
                return None
        else:
            return None
        if uid and ut:
            user, timestamp = User.get_by_auth_token(long(uid), ut)
            if user:
                return user
            else:
                return None
        else:
            return None

    def __auth_error(self):
        """
        this because exception is not handled correctly
        :return: render repsonse
        """
        self.response.headers['Content-Type'] = 'application/json'
        self.response.set_status(500, "auth error")
        self.response.write(json.encode({'error': 'auth failed'}))

    def dispatch(self):
        user = self.get_user()
        if user:
            self.request.user = user
            super(BaseJsonHandler, self).dispatch()
        else:
            self.__auth_error()
