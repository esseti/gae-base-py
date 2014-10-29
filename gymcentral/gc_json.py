import json
import logging

from gymcentral.exceptions import MissingParameters, DecodingParameter


__author__ = 'stefano'


# class JSONEncoder(json.JSONEncoder):
#
# def default(self, o):
#         # If this is a key, you might want to grab the actual model.
#         if isinstance(o, ndb.Key):
#             o = ndb.get(o)
#
#         if isinstance(o, ndb.Model):
#             return db.to_dict(o)
#         elif isinstance(o, (datetime, date, time)):
#             return str(o)  # Or whatever other date format you're OK with...

def deserialize_request(request, parameters=[]):
    """
    Transform the request into a json object.
    :param request: the request object
    :param parameter: the parameters that have to be in the result
    :return: The json object
    """
    if not isinstance(parameters, list):
        raise Exception("Parameters must be iterable")

    ret = {}

    for parameter in parameters:
        # logging.debug("par %s = %s " % (parameter, request.get(parameter)))
        value = request.get(parameter, default_value=None)
        logging.debug("req %s %s " % (parameter, value))
        if value:
            ret[parameter] = value
        else:
            raise MissingParameters(parameter, 404)
    return ret


def serialize_object(object, parameters=None):
    """
    Transform an ndb object into JSON
    :param object: an object
    :param parameters: list of parameters to put
    :return: the json
    """
    logging.debug("Object %s", object)
    ret = {}
    # get the dict
    od = object.to_dict()
    od['id'] = object.key.id()
    if parameters:
        for parameter in parameters:
            if parameter in od:
                if hasattr(od[parameter], 'isoformat'):
                    ret[parameter] = str(od[parameter])
                else:
                    ret[parameter] = od[parameter]
            # else:
            #     raise DecodingParameter(parameter, 404)
    else:
        for v in od:
            if hasattr(od[v], 'isoformat'):
                od[v] = str(od[v])
        ret = od
    return ret


def serialize_list(list, token=None, parameters=None):
    """
    Transform an list of ndb objects into JSON
    :param object: a list
    :param parameters: list of parameters to put
    :return: the json
    """
    ret = {}
    l = []
    for o in list:
        l.append(serialize_object(o, parameters))
    ret['objects'] = l
    if token:
        ret['nextPage'] = token
    return ret