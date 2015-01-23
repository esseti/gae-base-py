import json
import logging

import webapp2

import cfg
from gymcentral.exceptions import GCAPIException
from gymcentral.gc_utils import json_serializer, error


__author__ = 'stefano'
# credits go to Alex Vagin


class WSGIApp(webapp2.WSGIApplication):
    def __init__(self, *args, **kwargs):
        super(WSGIApp, self).__init__(*args, **kwargs)
        self.router.set_dispatcher(self.__class__.custom_dispatcher)

    @staticmethod
    def custom_dispatcher(router, request, response):
        # logging.debug("router %s", router)
        origin = request.headers.get('origin', '*')

        # STE: this is for cross orgin calls, correct? i should not need it.
        # Default response obj
        # JSON (or empty by still json content type) response
        # for 204 the content_type shouldn't be set..
        resp = webapp2.Response(content_type='application/json', charset='UTF-8')
        # if request.method == 'OPTIONS':
        # # CORS pre-flight request
        #     resp.auth_headers.update({
        #     'Access-Control-Allow-Credentials': 'true',
        #     'Access-Control-Allow-Origin': origin,
        #             'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
        #             'Access-Control-Allow-Headers': ('accept, origin, content-type, '
        #                                              'x-requested-with, cookie'),
        #             'Access-Control-Max-Age': str(cfg.AUTH_TOKEN_MAX_AGE)})
        #     return resp

        try:
            rv = router.default_dispatcher(request, response)

            if isinstance(rv, webapp2.Response):
                # if we want HTML then
                return rv
                # raise Exception("This type or response is not allowed")


            # STE: in case we want to specify the code
            if isinstance(rv, tuple):
                code, rv = rv
                resp.status = code
            if rv is not None:
                json.dump(rv, resp, default=json_serializer)

            # cache response if requested and possible
            # STE: i don't get this as well
            # if request.get('cache') and request.method in ('GET', 'OPTIONS'):
            #     exp_date = datetime.utcnow() + timedelta(seconds=cfg.API_CACHE_MAX_AGE)
            #     cache_ctrl = 'max-age=%d, must-revalidate' % cfg.API_CACHE_MAX_AGE
            #     resp.auth_headers.update({
            #         'Cache-Control': cache_ctrl,
            #         'Expires': exp_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
            #     })

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




