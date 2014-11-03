import logging

import cfg
from gymcentral.app import WSGIApp
from gymcentral.auth import GCAuth, user_required
from gymcentral.exceptions import BadRequest, MissingParameters
from gymcentral.utils import json_from_request
from models import User as m_User
# from models import Club as m_Club


__author__ = 'stefano'
# better way to write the api
# check the cfg file, it should not be uploaded!
app = WSGIApp(config=cfg.API_APP_CFG, debug=cfg.DEBUG)


@app.route('/myapi/test/<user_id>', methods=('GET',))
def get_test(req, user_id):
    user = m_User.query().get()
    return GCAuth.auth_user(user)


@app.route('/myapi/test/<param>', methods=('POST',))
@user_required
def update_custom(req, param):
    req_data = json_from_request(req)
    logging.debug("%s %s" % (type(req_data), req_data))
    if not 'test' in req_data:
        raise MissingParameters("ciao")
    req_data['param'] = param
    return req_data
