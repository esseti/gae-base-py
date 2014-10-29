import logging


from webapp2 import WSGIApplication
from webapp2_extras.appengine.auth.models import User
from gymcentral.exceptions import UserExists

from gymcentral.handlers import BaseJsonHandler, BaseJsonAuthHandler
from gymcentral.gc_json import serialize_object, deserialize_request, serialize_list


__author__ = 'stefano'

#TODO:
# - fix the authentication as explained in the link
#       user extra http://blog.abahgat.com/2013/01/07/user-authentication-with-webapp2-on-google-app-engine/
# - provide easy-to-use query request, with nextPageToken and size.
#

class UserList(BaseJsonHandler):
    # we have to manage the pagination here
    def get(self):
        users, token, hasnext = User.query().fetch_page(10)
        logging.debug("%s %s %s"%(users, token,hasnext))
        # is there a way to do this automatically?
        self.write_a_json(serialize_list(users, token=token.urlsafe(),parameters=['id','auth_ids']))

    def post(self):
        req = deserialize_request(self.request, ['username'])
        # user extra http://blog.abahgat.com/2013/01/07/user-authentication-with-webapp2-on-google-app-engine/
        res = User.create_user('own:'+req['username'])
        logging.debug("res %s",res)
        if not res[0]:
            raise UserExists
        else:
            self.write_a_json(serialize_object(res[1],['id','auth_ids']))


class UserDetails(BaseJsonAuthHandler):
    def get(self, user_id):
        logging.debug("User id %s", user_id)
        user = User.get_by_id(int(user_id))
        User.get_by
        logging.debug(user)
        if user:
            self.write_a_json(serialize_object(user))
        else:
            self.write_a_json("{'error':'not found'}")


app = WSGIApplication([
                          (r'/user/', UserList),
                          (r'/user/(?P<user_id>\d+)/', UserDetails)

                      ], debug=True)