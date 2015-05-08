from datetime import datetime
import logging
import logging.config

from google.appengine.ext import ndb
from google.appengine.ext.ndb import model
from webapp2_extras.appengine.auth.models import User, UserToken

from exceptions import ValidationError


__author__ = 'stefano'


class GCModel(ndb.Model):
    # This is to preserve the order
    created = ndb.DateTimeProperty(auto_now_add=True)

    @property
    def id(self):
        if self.key:
            return self.key.urlsafe()
        else:
            return None

    @property
    def safe_key(self):
        return self.key.urlsafe()

    def is_valid(self):
        # logging.warning("is_valid() should be implemented. Class: %s .. returning TRUE", self._class_name())
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

    @classmethod
    def get_by_id(cls, obj1):
        # like this we always use the key in safeurl
        k1 = obj1.key.safeurl() if hasattr(obj1, 'key') else obj1
        try:
            return ndb.Key(urlsafe=k1).get()
        except:
            return None

    def to_dict(self):
        result = super(GCModel, self).to_dict()
        result['id'] = self.id
        # this set to null the empty strings
        for key, value in result.iteritems():
            if isinstance(value, basestring) and not value:
                result[key] = None
        return result

    @property
    def active(self):
        if hasattr(self,'is_active'):
            return self.is_active
        else:
            return True

class GCModelMtoMNoRep(GCModel):
    # this class is used for MtoM relationship.
    # when creating the object, use YourClass(id=YourClass.build_id(obj1.key(),obj2.key())
    # THERE CANNOT BE REPETITION, since the same two objects returns the same id

    @staticmethod
    def __pair(n, m):
        # baratella: encoding of two numbers in an unique way.
        # NOTE: python does not have limits for that
        return ((n + m) * (n + m + 1) / 2) + n

    @classmethod
    def build_id(cls, obj1, obj2):
        k1 = obj1.key if hasattr(obj1, 'key') else obj1
        k2 = obj2.key if hasattr(obj2, 'key') else obj2
        return "%s|%s" % (k1.urlsafe(), k2.urlsafe())

    @classmethod
    def get_by_id(cls, obj1, obj2):
        k1 = obj1.key if hasattr(obj1, 'key') else obj1
        k2 = obj2.key if hasattr(obj2, 'key') else obj2
        return ndb.Key(cls, cls.build_id(obj1, obj2)).get()


class GCUserToken(UserToken):
    # add this field as indexed
    user = model.StringProperty(required=True)


class GCUser(GCModel, User):
    # new models
    token_model = GCUserToken

    @classmethod
    def create_auth_token(cls, user_id):
        """
        Create the token if None exists, otherwise provides back one that exists

        :param user_id: the user id
        :return: the token
        """
        token = cls.token_model.query(cls.token_model.user == str(user_id)).get()
        if token:
            token.updated = datetime.now()
            token.put()
            return token.token
        else:
            return cls.token_model.create(user_id, "auth").token
