import cgi
import json
from functools import wraps
from wsgiref.simple_server import make_server
try:
    import httplib
except ImportError:
    import http.client as httplib  # py3


class Request(object):
    """
    Initiates a request object given the environ from the server
    """

    def __init__(self, environ):
        self.environ = environ
        self.headers = self._parse_headers(environ)
        self.query = self._parse_query(environ)
        self.data = self._parse_data(environ)

    def _parse_query(self, environ):
        query = cgi.parse_qs(environ['QUERY_STRING'])
        return {k: v[0] for k, v in query.items()}

    def _parse_headers(self, environ):
        length = environ.get('CONTENT_LENGTH', 0)
        headers = {'CONTENT_LENGTH': 0 if not length else int(length)}

        wanted_headers = ['REQUEST_METHOD', 'PATH_INFO', 'REMOTE_ADDR',
                          'REMOTE_HOST', 'CONTENT_TYPE']

        for k, v in environ.items():
            if k in wanted_headers or k.startswith('HTTP'):
                headers[k] = v
        return headers

    def _parse_data(self, environ):
        content_type = environ['CONTENT_TYPE'].lower()
        data = {}
        if 'form' in content_type:
            env_data = cgi.FieldStorage(environ['wsgi.input'],
                                        environ=environ)
            for k in env_data.list:
                # filter out url queries
                if not isinstance(k, cgi.MiniFieldStorage):
                    if k.filename:
                        data[k.name] = k.file
                    else:
                        data[k.name] = k.value
            return data
        else:
            length = self.headers['CONTENT_LENGTH']
            return environ['wsgi.input'].read(length)


class Response(object):
    """
    Response object is responsable for initiating the make_response and returning the view data
    :params code, the status code
    :params data, the raw data rendered from the view

    """
    def __init__(self, make_response, code=200, data=''):
        # view can return str or str and a dict of headers
        if isinstance(data, tuple):
            self.data = data[0]
            headers = data[1]
        else:
            self.data = data
            headers = {}

        if 'content-type' not in map(lambda x: x.lower(), headers):
            headers['Content-Type'] = 'text/html'

        self.headers = [(k, v) for k, v in headers.items()]
        self.code = code
        self.make_response = make_response

    def render(self):
        resp_code = '{} {}'.format(self.code, httplib.responses[self.code])

        if str(self.code)[0] in ['4', '5']:
            self.make_response(resp_code, self.headers)
            yield resp_code.encode('utf-8')

        try:
            data = bytes(self.data)
        except Exception:
            data = str(self.data).encode('utf-8')

        self.make_response(resp_code, self.headers)
        yield data


class App(object):

    def __init__(self):
        self.routes = {}

    def route(self, url, methods=['GET']):

        def decorate(f):

            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)

            self.routes[url] = {'methods': methods, 'func': wrapper}

            return wrapper
        return decorate

    def path_dispatch(self, request, make_response):
        path = request.headers['PATH_INFO']
        method = request.headers['REQUEST_METHOD']
        view = self.routes.get(path)
        if not view:
            response = Response(make_response, 404)
        elif method not in view['methods']:
            response = Response(make_response, 405)
        else:
            data = view['func'](request)
            response = Response(make_response, data=data)

        return response

    def dispatch_request(self, environ, make_response):
        request = Request(environ)
        response = self.path_dispatch(request, make_response)
        return response

    def __call__(self, environ, make_response):
        """The actual wsgi app"""
        resp = self.dispatch_request(environ, make_response)
        return resp.render()


    def run(self, host='', port=8080):
        """ server """
        httpd = make_server(host, port, self)
        print('Serving on {host}:{port}'.format(host=host, port=port))
        httpd.serve_forever()
