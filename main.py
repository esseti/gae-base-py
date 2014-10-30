import logging

from webapp2 import WSGIApplication
from webapp2_extras.appengine.auth.models import User

from gymcentral.exceptions import UserExists
from gymcentral.handlers import BaseJsonHandler, BaseJsonAuthHandler


__author__ = 'stefano'

# TODO:
# - fix the authentication as explained in the link
# user extra http://blog.abahgat.com/2013/01/07/user-authentication-with-webapp2-on-google-app-engine/
# - provide easy-to-use query request, with nextPageToken and size.
#


class UserList(BaseJsonHandler):
    # FIXME: how to specify request inputs for each method?

    # we have to manage the pagination here
    def get(self):
        # self.set_in_pars(['id'])
        logging.debug("req %s", self.request.in_dict)
        self.set_out_pars(['id', 'username'])

        users, token, hasnext = User.query().fetch_page(10)
        # logging.debug("%s %s %s"%(users, token,hasnext))
        self.render(users, token=123)
        # is there a way to do this automatically?


    def post(self):
        self.set_in_pars(['username'])
        self.set_out_pars(['id', 'token'])
        in_dict = self.request.in_dict

        res = User.create_user('own:' + in_dict['username'], username=in_dict['username'],unique_properties=['username'])
        logging.debug("res %s", res)
        if not res[0]:
            raise UserExists
        else:
            user = res[1]
            self.auth_user(user)
            self.render(user)


class UserDetails(BaseJsonHandler):
    def get(self, user_id):
        # This just autorize this id. used for testing
        logging.debug("User id %s", user_id)
        # FIXME: why i've to convert to int?
        user = User.get_by_id(int(user_id))
        self.auth_user(user)
        self.render(user)


class UserMe(BaseJsonAuthHandler):
    def get(self):
        logging.debug("in me")
        user = self.request.user
        logging.debug(user)
        self.render(user)


app = WSGIApplication([

                          (r'/user/', UserList),
                          (r'/user/me/', UserMe),
                          (r'/user/(?P<user_id>\d+)/', UserDetails),


                      ], debug=True)