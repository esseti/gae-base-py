import json
from urllib import urlencode
import urllib2
from decorator import decorator

from google.appengine.api import urlfetch
from webapp2_extras.securecookie import SecureCookieSerializer

import cfg
from gymcentral.exceptions import AuthenticationError










# TODO: change this to your app.
import models


__author__ = 'stefano'


class GCAuth():
    """
    Class that manages the Authorization

    TODO: create a cron job that deletes old/expired tokens
    """

    __user_model = models.User
    __config_file = cfg
    __app_name = "gc"

    @classmethod
    def get_secure_cookie(cls, token):
        scs = SecureCookieSerializer(cls.__config_file.API_APP_CFG[cls.__app_name]['SECRET_KEY'])
        token = scs.serialize('Token', token)
        return token

    @classmethod
    def get_token(self, token):
        return {"token": token}

    @classmethod
    def auth_user_token(cls, user):
        """
        get the token of the current user

        :param user
        :return: token
        """
        user_id = user.get_id()
        user_token = cls.__user_model.create_auth_token(user_id)
        token = str(user_id) + "|" + user_token
        return token

    @classmethod
    def get_user_or_none(cls, req):
        """
        actual method that return the user or ``None``

        :param req:
        :return:
        """

        uid = None
        ut = None
        # # in case it's test. use remote user.
        # if 'REMOTE_USER' in req.environ and cls.__config_file.DEBUG:
        # token = req.environ['REMOTE_USER']
        # uid, ut = token.split("Token")[1].split("|")
        # even if in test, but the remote user is not found. then...
        if not uid and not ut:
            token = req.headers.get("Authorization")
            if token:
                ret_token = token.split("Token")[1]
                if not ret_token:
                    return None
                uid, ut = ret_token.split("|")
            else:
                scs = SecureCookieSerializer(cls.__config_file.API_APP_CFG[cls.__app_name]['SECRET_KEY'])
                token = req.cookies.get('gc_token')
                if token:
                    token_des = scs.deserialize('Token', token)
                    if not token_des:
                        return None
                    uid, ut = token_des.split("|")
                else:
                    return None
        if uid and ut:
            # user = memcache.get("%s|%s" % (uid, ut))
            # if user:
            # return user
            # else:
            if cls.__user_model.validate_auth_token(long(uid), ut):
                user = cls.__user_model.get_by_auth_token(long(uid), ut)[0]
                return user
                # store in memcace for 1 week
                # memcache.set("%s|%s" % (uid, ut), user, time=60 * 24 * 7)
        return None

    @classmethod
    def get_user(cls, req):
        """
        Get the user from the authorization.

        :return: the user or None
        """
        user = cls.get_user_or_none(req)
        if user:
            return user
        else:
            raise AuthenticationError("Auth error")


    @staticmethod
    def handle_oauth_callback(access_token, provider):
        '''
        this function takes teh access_token and the provider and return the dictionary of the user

        :param access_token:
        :param provider:
        :return: a triple: the user data, the acess_token, and the error message (if any)
        '''

        if provider == 'facebook':
            url = "https://graph.facebook.com/me?access_token=" + access_token
            return json.loads(urllib2.urlopen(url).read()), access_token, None
        elif provider == 'google':
            url = 'https://www.googleapis.com/oauth2/v3/userinfo?{0}'
            target_url = url.format(urlencode({'access_token': access_token}))
            resp = urlfetch.fetch(target_url).content
            user_data = json.loads(resp)
            if 'id' not in user_data and 'sub' in user_data:
                user_data['id'] = user_data['sub']
            return user_data, access_token, None
        else:
            return None, None, 'invalid provider'


# TODO add wrapper to check if user is member and of what type
@decorator
def user_required(handler):
    """
    Decorator to check that user is logged in via Authorization Token

    :param handler:
    :return: ``User`` or ``None``
    """
    def wrapper(req, *args, **kwargs):
        user = GCAuth.get_user(req)
        if user is None:
            raise AuthenticationError
        req.user = user
        return handler(req, *args, **kwargs)

    return wrapper
