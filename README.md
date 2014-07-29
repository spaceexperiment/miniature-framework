wsgi application with route decorator
=====================================

In 174 lines of code, with no external dependencies

Example usage
``` python
@app.route('/form', methods=['POST'])
def form():
	# do something with form files
    # app.request.files

    # do something with form fields data
    # app.request.data

    return 'submitted successfully'

```

See example_app.py for more examples
