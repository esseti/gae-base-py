from datetime import datetime
import logging
import logging.config

from google.appengine.ext import ndb
from google.appengine.ext.ndb import model
from webapp2_extras.appengine.auth.models import User, UserToken

from exceptions import ValidationError


__author__ = 'stefano'

"""
We define models class with handy function to be used while developing
"""

class GCModel(ndb.Model):
    """
    The standard model class.

    - id: that return the urlsafe of the key
    - safe_key: the same as id
    - is_valid: to be used in the put. This function can be rewritten by the models that extends this class to implement validation and in case fail the put function
    - put: rewrites the `put`. If validation fails the put is not performed.
    - get_by_id: easy method to retreive the object, can be a key or a urlsafe key
    - to_dict: to transform the object into a dictionary. note: Set emtpy string as `None`
    - is_active: returns if a model is active, can be overwritten.
    """


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
    """
    Class for the MtoM relation with No repetition.
    It creates a key that is unique for the two pairs. So that there's no repetition.

    ..warning::
        A,B and B,A returns two different objects. respect the order.

    """
    # this class is used for MtoM relationship.
    # when creating the object, use YourClass(id=YourClass.build_id(obj1.key(),obj2.key())
    # THERE CANNOT BE REPETITION, since the same two objects returns the same id

    @staticmethod
    def __pair(n, m):
        # encoding of two numbers in an unique way.
        # expensive, better use build_id
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
    """
    User model,

    extends the GCModel and standard user. Add a function to create the auth token.
    """
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
