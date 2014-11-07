import logging

from google.appengine.ext import ndb
from webapp2_extras.appengine.auth.models import User

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
        logging.warning("is_valid() should be implemented. Class: %s", self._class_name())
        return True


    def put(self):
        """
        use this instead of put
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


class GCUser(GCModel, User):
    def is_valid(self):
        return True