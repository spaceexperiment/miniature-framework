from wsgi import App


app = App()


@app.route('/')
def home():
    print('test')
    return 'Home page'


@app.route('/json', methods=['POST'])
def post():
    return app.request.json

@app.route('/form', methods=['POST'])
def form():
    print(len(app.request.files))
    return app.request.data

@app.route('/data', methods=['POST'])
def data():
    # text data, not form or json
    return app.request.data

@app.route('/cookie')
def cookie():
    # set headers
    app.headers = {'Content-Type': 'application/json',
                   'Set-Cookie': 'user=me; path=/;'}

    return app.request.headers.get('HTTP_COOKIE', 'No cookie')


if __name__ == '__main__':
    app.run()
