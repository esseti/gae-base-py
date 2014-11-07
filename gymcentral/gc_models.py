import logging

from google.appengine.ext import ndb
from google.appengine.ext.ndb.query import Cursor
from webapp2_extras.appengine.auth.models import User

import cfg
from gymcentral.exceptions import ValidationError


__author__ = 'stefano'


class GCModel(ndb.Model):
    @property
    def id(self):
        return self.key.id()

    @property
    def safe_key(self):
        return self.key.urlsafe()

    def is_valid(self):
        raise Exception(".is_valid() must be implemented")

    def put(self):
        """
        use this instead of put
        :param ctx_options:
        :return:
        """
        res = self.is_valid()
        if isinstance(res, (list, tuple)):
            validation, field = res
        else:
            validation = res
            field = "unknown"
        if validation:
            self._put()
        else:
            raise ValidationError(field)

    @classmethod
    def get_all_objects(cls):
        return cls.get(cls.query())

    @classmethod
    def get_all_objects_paginated(cls, start_cursor=None):
        return cls.get(cls.query(), paginated=True, cursor=start_cursor)

    @staticmethod
    def total(o):
        if isinstance(o, ndb.Query):
            return o.count()
        elif isinstance(o, list):
            return len(o)
        else:
            raise Exception("Type not found")

    @staticmethod
    def get(o, paginated=False, size=-1, cursor=None):
        """
        Implements the get given an object
        :param o: the object
        :param paginate: if the result has to be paginated
        :param size: the size of the page or of the number of elements to retrive
        :param cursor: the starting poin in case of pagination
        :return: the list of objects, next_page token, if has next page, size; or the object in case it's one
        """
        # if result has to be paginated
        if not paginated:
            # if it's a query, then use fetch
            if isinstance(o, ndb.Query):
                if size == -1:
                    return o.fetch()
                return o.fetch(size)
            elif isinstance(o, list):
                if len(o) > size:
                    size = len(o)
                if size == -1:
                    size = cfg.PAGE_SIZE
                # crop the list
                ret = o[:size]
                return ret
            else:
                logging.debug("Type %s %s", type(o), o)
                raise Exception("Type not found %s %s"%(type(o),o))
        else:
            # in case the size is not specified, then it's -1 we use the value in the config
            if size == -1:
                size = cfg.PAGE_SIZE
            # if it's a query, we use ndb
            if isinstance(o, ndb.Query):
                if cursor:
                    data, token, has_next = o.fetch_page(size, start_coursor=Cursor(urlsafe=cursor))
                    if token:
                        token = token.url_safe()
                    return data, token, has_next, o.count()
                else:
                    data, token, has_next = o.fetch_page(size)
                if token:
                    token = token.urlsafe()
                return data, token, has_next, o.count()
            # else we do our case.
            elif isinstance(o, list):
                if not cursor:
                    cursor = 1
                if cursor < 1:
                    cursor = 1
                start = (cursor - 1) * size
                end = cursor * size
                logging.debug("%s %s" % (start, end))
                # crop the list
                res_list = o[start:end]
                # create the object
                # it's probably another page
                next_page = None
                if len(res_list) == size:
                    next_page = str(cursor + 1)
                res = ndb.get_multi(res_list)
                logging.debug("%s %s" % (res_list, res))
                if next_page:
                    return res, next_page, True, len(o)
                else:
                    return res, None, False, len(o)
            else:
                logging.debug("Type %s %s", type(o), o)
                raise Exception("Type not found")


class GCUser(GCModel, User):
    def is_valid(self):
        return True