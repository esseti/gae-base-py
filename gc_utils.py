import webapp2

__author__ = 'stefano'
import logging
import json
from datetime import datetime
import time

from google.appengine.ext import ndb
from google.appengine.ext import blobstore

from gymcentral.exceptions import BadRequest, MissingParameters


__author__ = 'stefano'

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


def __camel_string(snake_str):
    '''
    convert snake string to camelString
    e.g., hello_world -> helloWorld
    :param snake_str: the snake string
    :return: the camleString
    '''
    components = snake_str.split('_')
    return components[0] + "".join(x.title() for x in components[1:])


def __camel_case(d):
    '''
    utils to transform the dictionary fields from snake to camel case
    :param d:
    :return:
    '''
    ret_camel = {}
    for e in d:
        ret_camel[__camel_string(e)] = d[e]
    return ret_camel


def sanitize_json(data, allowed=[], hidden=[]):
    '''
    Takes a dict in input and returns a dict  that contains only allowed fields, hiding the  the hidden fields
    :param data: the dict
    :param allowed: the allowed fields
    :param hidden: the list of fields to hide
    :return: a dict
    '''
    ret = {}
    if allowed:
        for attr in allowed:
            if attr in data:
                ret[attr] = data[attr]
            else:
                raise MissingParameters(attr)
    else:
        ret = data
    # even if allowed and hidden are specified this will work.
    for rem in hidden:
        if rem in ret:
            del ret[rem]
    # convert to camel case to be compiant with Json standard
    ret = __camel_case(ret)
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
    __items = (('page', 1), ('size', -1)) + pars
    ret = {}
    for item in __items:
        ret[item[0]] = req.get(item[0], item[1])
    return ret


def json_from_request(req, *allowed_props):
    '''
    Takes in input the request and creates a dict that contains the allowed properties.
    :param req: the request object
    :param allowed_props: list of properties that the object has to contain.
    :return: json object
    '''
    if req.body:
        try:
            logging.debug("body %s", req.body)
            data = json.loads(req.body)
            if allowed_props:
                sanitize_json(data, allowed=allowed_props)
            return data
        except (TypeError, ValueError) as e:
            logging.error(e)
            raise BadRequest("Invalid JSON")
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
        # adding the id if possible
        if hasattr(obj, 'id'):
            to_dict['id'] = obj.id
        # do not return emtpy fields.
        # return dict((k, v) for k, v in to_dict.iteritems() if v)
        return to_dict
    elif isinstance(obj, list):
        ret = []
        for o in obj:
            ret.append(json_serializer(o))
        return ret
    else:
        return obj