from datetime import datetime, timedelta
import json
import logging
import logging.config
import webapp2

import cfg
from gymcentral.exceptions import GCAPIException
from gymcentral.gc_utils import json_serializer, error
from gymcentral.http_codes import GCHttpCode


__author__ = 'stefano'
# credits go to Alex Vagin

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('myLogger')


class WSGIApp(webapp2.WSGIApplication):
    def __init__(self, *args, **kwargs):
        super(WSGIApp, self).__init__(*args, **kwargs)
        self.router.set_dispatcher(self.__class__.custom_dispatcher)

    @staticmethod
    def edit_request(router, request, response):
        return request

    @staticmethod
    def edit_response(rv):
        return rv

    @staticmethod
    def custom_dispatcher(router, request, response):

        origin = request.headers.get('origin', '*')

        resp = webapp2.Response(content_type='application/json', charset='UTF-8')
        if request.method == 'OPTIONS':
            # CORS pre-flight request
            resp.headers.update({'Access-Control-Allow-Credentials': 'true',
                                 'Access-Control-Allow-Origin': origin,
                                 'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
                                 'Access-Control-Allow-Headers': ('accept, origin, content-type, '
                                                                  'x-requested-with, cookie'),
                                 'Access-Control-Max-Age': str(cfg.AUTH_TOKEN_MAX_AGE)})
            return resp

        try:
            app = webapp2.get_app()
            request = app.edit_request(router, request, response)
            rv = router.default_dispatcher(request, response)
            rv = app.edit_response(rv)
            if isinstance(rv, webapp2.Response):
                return rv

            if isinstance(rv, GCHttpCode):
                resp.status = rv.code
                rv = rv.message

            # STE: in case we want to specify the code
            if isinstance(rv, tuple):
                code, rv = rv
                resp.status = code
            if rv is not None:
                json.dump(rv, resp, default=json_serializer)

            # cache response if requested and possible
            if request.get('cache') and request.method in ('GET', 'OPTIONS'):
                exp_date = datetime.utcnow() + timedelta(seconds=cfg.API_CACHE_MAX_AGE)
                cache_ctrl = 'max-age=%d, must-revalidate' % cfg.API_CACHE_MAX_AGE
                resp.headers.update({
                    'Cache-Control': cache_ctrl,
                    'Expires': exp_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
                })

            resp.headers.update({
                'Access-Control-Allow-Origin': origin,
                'Access-Control-Allow-Credentials': 'true'})

        except GCAPIException as ex:
            if hasattr(ex, 'code'):
                resp.status = ex.code
            else:
                resp.status = 400
            msg = str(ex)
            if cfg.DEBUG:
                logging.exception(ex)
            elif msg:
                logging.error(msg)
            add_args = []
            if hasattr(ex, 'field'):
                add_args.append(('field', ex.field))
            json.dump(error(msg, code=resp.status_int, add_args=add_args), resp)
        except Exception as e:
            if hasattr(e, 'code'):
                resp.status = e.code
            else:
                resp.status = 500
            # for other execptions, return 500 error and log it internally
            msg = str(e)
            if cfg.DEBUG:
                logging.exception(msg)
            elif msg:
                logging.error(msg)
            add_args = [('exception_message', msg)]
            json.dump(error("Internal Server Error", code=500, add_args=add_args), resp)
        return resp

    def route(self, *args, **kwargs):
        def wrapper(func):
            self.router.add(webapp2.Route(handler=func, *args, **kwargs))
            return func

        return wrapper




