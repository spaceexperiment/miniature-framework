from wsgi import App


app = App()

@app.route('/')
def home():
    print(app.request.get)
    return 'Home page'


@app.route('/json', methods=['POST'])
def post():
    return app.request.json


@app.route('/form', methods=['POST'])
def form():
    print(app.request.files)
    return app.request.data


@app.route('/data', methods=['POST'])
def data():
    # text data, not form or json
    return app.request.data


@app.route('/setcookie')
def set_cookie():
    # set headers
    app.headers = {'Content-Type': 'application/json',
                   'Set-Cookie': 'user=marv; pass=$@#!; path=/;'}

    return 'cookies set'


@app.route('/getcookie')
def get_cookie():
    return app.request.headers.get('HTTP_COOKIE', 'No cookies :(')


if __name__ == '__main__':
    app.run()
