import json
import logging
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from gymcentral.exceptions import BadRequest

from datetime import datetime, time

__author__ = 'stefano'

_DEFAULT_ERROR_MSG = 'An error occurred while processing this request'

def error(msg, code=400):
    return {
        'error': {
            'message': (msg or _DEFAULT_ERROR_MSG),
            'code': code
        }
    }


def sanitize_json(data, *allowed_props):
    for attr in list(data):
        if attr not in allowed_props:
            del data[attr]


def json_from_request(req, *allowed_props):
    try:
        data = json.loads(req.body)
        if allowed_props:
            sanitize_json(data, *allowed_props)
        return data
    except (TypeError, ValueError) as e:
        logging.error(e)
        raise BadRequest('Invalid JSON data')


def json_serializer(obj):
    if isinstance(obj, datetime):
        return int(time.mktime(obj.utctimetuple()) * 1e3 + obj.microsecond / 1e3)
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif isinstance(obj, ndb.Key):
        return obj.urlsafe()  # obj.id()
    elif isinstance(obj, blobstore.BlobKey):
        return str(obj)
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    else:
        return obj