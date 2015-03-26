import json

__author__ = 'stefano'
from datetime import datetime
import time
import re

from google.appengine.ext import ndb

from google.appengine.ext import blobstore

from exceptions import BadRequest, MissingParameters


_DEFAULT_ERROR_MSG = 'An error occurred while processing this request'


def error(msg, code=400, add_args=[]):
    """
    renders the execption

    :param msg: the message
    :param code: the status code
    :param add_args: additonal arguments added to the error message
    :return: the dict of the exception ready to be rendered
    """
    ret = {}
    ret['error'] = {
        'message': (msg or _DEFAULT_ERROR_MSG),
        'code': code
    }
    for arg in add_args:
        ret['error'][arg[0]] = arg[1]
    return ret


def sanitize_list(data, allowed=[], hidden=[]):
    '''
    Takes a list in input and returns a list of dict that contains only allowed fields, hiding the  the hidden fields

    :param data: the list
    :param allowed: the list of allowed fields
    :param hidden: the list of fields to hide
    :return: a list of dicts
    '''
    ret = []
    for d in data:
        ret.append(sanitize_json(d, allowed, hidden))
    return ret


def __snake_string(snake_str):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', snake_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def __snake_case(d):
    snake_camel = {}
    for e in d:
        if isinstance(d[e], dict):
            snake_camel[__snake_string(e)] = __snake_case(d[e])
        else:
            snake_camel[__snake_string(e)] = d[e]
    return snake_camel


def __camel_string(snake_str):
    '''
    convert snake string to camelString

    e.g., hello_world -> helloWorld

    :param snake_str: the snake string
    :return: the camleString
    '''
    components = snake_str.split('_')
    return components[0] + "".join(x.title() for x in components[1:])


def __camel_list(l):
    res = []
    for el in l:
        res.append(camel_case(el))
    return res


def __camel_dict(d):
    res = {}
    for e in d:
        res[__camel_string(e)] = camel_case(d[e])
    return res


def camel_case(d):
    '''
    utils to transform the dictionary fields from snake to camel case

    :param d:
    :return:
    '''
    # ret_camel = {}
    if isinstance(d, list):
        return __camel_list(d)
    elif isinstance(d, dict):
        return __camel_dict(d)
    elif isinstance(d, ndb.Model):
        # this happens when there's structured properties..
        return __camel_dict(d.to_dict())
    else:
        return d


def sanitize_json(data, allowed=[], hidden=[], except_on_missing=True):
    '''
    Takes a dict or a Model in input and returns a dict  that contains only allowed fields, hiding the  the hidden fields

    :param data: the dict
    :param allowed: the allowed fields
    :param hidden: the list of fields to hide
    :return: a dict
    '''
    if isinstance(data, ndb.Model):
        data = data.to_dict()
    ret = {}
    if allowed:
        for attr in allowed:
            if attr in data:
                ret[attr] = data[attr]
            else:
                if except_on_missing:
                    raise MissingParameters(attr)
    else:
        ret = data
    # even if allowed and hidden are specified this will work.
    for rem in hidden:
        if rem in ret:
            del ret[rem]
    # convert to camel case to be compiant with Json standard
    return ret


def json_from_paginated_request(req, pars=()):
    '''
    Takes the request in input and creates a dictionary that contains:
    - the parameters for paginated requests.
    - additional parameters specified by the developer as list of tuples: name, default_value.

    :param req: the request object
    :param pars: additional parameters as list of tuples
    :return:
    '''
    # if it's found then the value, otherwise the default
    __items = (('page', 0), ('size', -1)) + pars
    ret = {}
    for item in __items:
        if isinstance(item, tuple):
            name, value = item
        else:
            name, value = item, None
        ret[name] = req.get(name, value)
    return ret


def json_from_request(req, mandatory_props=None, optional_props=None, accept_all=False):
    '''
    Takes in input the request and creates a dict that contains the mandatory and optional properties.

    :param req: the request object
    :param mandatory_props: list of mandatory properties that the object HAS to contain.
    :param optional_props: list of optional properties that the object MAY  contain. Each item can be a
    tuple of name and default value e.g., ("myList",[]). *NB:* if the value is
    ``None the properties will NOT be added to the dict``
    :param accept_all: if ``True`` the request will accept any kind of input,
    yet check on mandatory and optional will be performed
    :return: json object
    '''
    if req.body:
        d = req.body
        try:
            j_req = json.loads(d)
        except (TypeError, ValueError) as e:
            raise BadRequest("Invalid JSON")
        if accept_all:
            data = j_req
        else:
            data = dict()
        if mandatory_props:
            for mandatory in mandatory_props:
                value = j_req.get(mandatory, None)
                if value is None:
                    raise MissingParameters(mandatory)
                else:
                    data[mandatory] = value
        if optional_props:
            for optional in optional_props:
                if isinstance(optional, tuple):
                    name, value = optional
                    get_value = j_req.get(name, value)
                    # if default value i None then we set as None
                    data[name] = get_value
                else:
                    name, value = optional, None
                    get_value = j_req.get(name, value)
                    # if there's no default value we set only if exists
                    if get_value is not None:
                        data[name] = get_value

        return __snake_case(data)

    else:
        if mandatory_props:
            raise MissingParameters(", ".join(mandatory_props))
        else:
            return {}


def json_serializer(obj):
    '''
    serialize an object to a dict.

    :param obj: the object
    :return: the dict
    '''
    # NOTE: this is also called when the app dumps the json, so be careful when editing
    # @propery are not rendered
    if isinstance(obj, datetime):
        return int(time.mktime(obj.utctimetuple()) * 1e3 + obj.microsecond / 1e3)
    elif isinstance(obj, ndb.Key):
        return obj.urlsafe()
    elif isinstance(obj, blobstore.BlobKey):
        return str(obj)
    elif hasattr(obj, 'to_dict'):
        to_dict = obj.to_dict()
        return to_dict
    elif isinstance(obj, list):
        ret = []
        for o in obj:
            ret.append(json_serializer(o))
        return ret
    else:
        return obj


def date_to_js_timestamp(obj):
    return int(time.mktime(obj.utctimetuple()) * 1e3 + obj.now().microsecond / 1e3)


def date_from_js_timestamp(obj):
    return datetime.fromtimestamp(long(obj) / 1000)