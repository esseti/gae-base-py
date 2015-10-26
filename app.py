from datetime import datetime, timedelta
import json
import logging
import logging.config

import webapp2

import cfg
from exceptions import GCAPIException
from gc_utils import json_serializer, error
from http_codes import GCHttpCode

__author__ = 'stefano'


# credits go to Alex Vagin


class WSGIApp(webapp2.WSGIApplication):
    # extension of the WSGI app with handy functionalities

    def __init__(self, *args, **kwargs):
        super(WSGIApp, self).__init__(*args, **kwargs)
        self.router.set_dispatcher(self.__class__.custom_dispatcher)

    @staticmethod
    def edit_request(router, request, response):
        # these methods are overridden when needed by subclasses.
        # GC overrides this to fill in the model in the request.
        return request

    @staticmethod
    def edit_response(rv):
        # this methods are overridden when needed by subclasses
        # GC overrides this to apply camel_case
        return rv

    @staticmethod
    def custom_dispatcher(router, request, response):

        # the origin, for CORS reqests
        origin = request.headers.get('origin', '*')
        origin = "*"

        resp = webapp2.Response(content_type='application/json', charset='UTF-8')

        if request.method == 'OPTIONS':
            # CORS pre-flight request
            # add x-app-id
            resp.headers.update({'Access-Control-Allow-Credentials': 'true',
                                 'Access-Control-Allow-Origin': origin,
                                 'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
                                 'Access-Control-Allow-Headers': ('accept, origin, content-type, '
                                                                  'x-requested-with, cookie, '
                                                                  'x-app-id, authorization'),
                                 'Access-Control-Max-Age': str(cfg.AUTH_TOKEN_MAX_AGE)})
            return resp

        try:
            app = webapp2.get_app()
            # always call this function, so if needed there can be changes applied before working on the request
            request = app.edit_request(router, request, response)
            # apply the dispatch
            rv = router.default_dispatcher(request, response)
            # edit the response if needed
            rv = app.edit_response(rv)
            # if is a plain response, then it's returned.
            if isinstance(rv, webapp2.Response):
                return rv
            # if it's a GCHttpCode, then return the message.
            if isinstance(rv, GCHttpCode):
                resp.status = rv.code
                if rv.code == 204:
                    resp.content_type = None
                rv = rv.message

            # STE: in case we want to specify the code
            if isinstance(rv, tuple):
                code, rv = rv
                resp.status = code
            if rv is not None:
                json.dump(rv, resp, default=json_serializer)

            # cache response if requested and possible
            if request.get('cache') and request.method in ('GET', 'OPTIONS'):
                exp_date = datetime.now() + timedelta(seconds=cfg.API_CACHE_MAX_AGE)
                cache_ctrl = 'max-age=%d, must-revalidate' % cfg.API_CACHE_MAX_AGE
                resp.headers.update({
                    'Cache-Control': cache_ctrl,
                    'Expires': exp_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
                })

        # in case of exception return a json and log accordingly
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
                logging.exception(msg)
            add_args = [('exception_message', msg)]
            json.dump(error("Something went wrong", code=500, add_args=add_args), resp)

        # move them here, so we can give back errors also for CORS 
        resp.headers.update({
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Credentials': 'true'})
        return resp

    def route(self, *args, **kwargs):
        def wrapper(func):
            self.router.add(webapp2.Route(handler=func, *args, **kwargs))
            return func

        return wrapper
