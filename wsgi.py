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
        self.headers = self._parse_headers(environ)
        self.get = self._parse_query(environ)
        self.data = {}
        self.files = {}
        self.json = None
        self.set_headers = {}
        self._parse_data(environ)

    def _parse_query(self, environ):
        query = cgi.parse_qs(environ['QUERY_STRING'])
        return {k: v[0] for k, v in query.items()}

    def _parse_headers(self, environ):
        length = environ.get('CONTENT_LENGTH', 0)
        length = 0 if not length else int(length)
        headers = {'CONTENT_LENGTH': length}

        wanted_headers = ['REQUEST_METHOD', 'PATH_INFO', 'REMOTE_ADDR',
                          'REMOTE_HOST', 'CONTENT_TYPE']

        for k, v in environ.items():
            if k in wanted_headers or k.startswith('HTTP'):
                headers[k] = v
        return headers

    def _parse_data(self, environ):
        content_type = environ['CONTENT_TYPE'].lower()
        if 'form' in content_type:
            env_data = cgi.FieldStorage(environ['wsgi.input'],
                                        environ=environ)
            for k in env_data.list:
                # filter out url queries
                if not isinstance(k, cgi.MiniFieldStorage):
                    if k.filename:
                        self.files[k.name] = k.file
                    else:
                        self.data[k.name] = k.value

        elif 'json' in content_type:
            length = self.headers['CONTENT_LENGTH']
            data = environ['wsgi.input'].read(length)
            data = data.decode('utf-8').strip('\'')
            try:
                self.json = json.loads(data)
            except ValueError:
                # todo return error invalid json
                print('error')
                pass

        else:
            length = self.headers['CONTENT_LENGTH']
            self.data = environ['wsgi.input'].read(length)


class Response(object):
    """
    Response object is responsable for setting the headers,
     cookie and response code.
    then initiating the make_response and returning the view data
    :params request, the request object, we input this AFTER we render
        the view, so that we can implement the user specified header...
    :params code, the status code
    :params data, the raw data rendered from the view

    """
    def __init__(self, request, code=200, data=''):
        headers = request.set_headers
        # todo set_cookie

        if 'content-type' not in map(lambda x: x.lower(), headers):
            headers['Content-Type'] = 'text/html'

        self.headers = [(k, v) for k, v in headers.items()]
        self.request = request
        self.data = data
        self.code = code

    def render(self):
        resp_code = '{} {}'.format(self.code, httplib.responses[self.code])

        def make_response(code):
            self.request.make_response(code, self.headers)

        if str(self.code)[0] in ['4', '5']:
            make_response(resp_code)
            return '<h1>{}</h1>'.format(resp_code).encode('utf-8')

        make_response(resp_code)
        return self.data


class App(object):

    def __init__(self):
        self.routes = {}
        self.request = None

    @property
    def headers(self):
        return self.request.headers

    @headers.setter
    def headers(self, value):
        self.request.set_headers = value

    def route(self, url, methods=['GET']):
        """
        Example usage

        @app.route('/home')
        def home():
            return 'Welcome home'
        """

        def decorate(f):

            @wraps(f)
            def wrapper(*args, **kwargs):
                try:
                    results = bytes(f(*args, **kwargs))
                except Exception:
                    results = str(f(*args, **kwargs)).encode('utf-8')
                return results

            self.routes[url] = {'methods': methods, 'render': wrapper}

            return wrapper
        return decorate

    def path_dispatch(self):
        path = self.request.headers['PATH_INFO']
        self.method = self.request.headers['REQUEST_METHOD']
        view = self.routes.get(path)
        print('1')
        if not view:
            response = Response(self.request, 404)
        elif self.method not in view['methods']:
            response = Response(self.request, 405)
        else:
            data = view['render']()
            response = Response(self.request, data=data)

        return response

    def dispatch_request(self, environ):
        self.request = Request(environ)
        self.response = self.path_dispatch()

    def __call__(self, environ, make_response):
        """The actual wsgi app"""

        self.dispatch_request(environ)
        self.request.make_response = make_response
        yield self.response.render()

    def run(self, host='', port=8080):
        """ server """
        httpd = make_server(host, port, self)
        print('Serving on localhost:8080')
        httpd.serve_forever()
