
# busreport.code4jc.org

from flask import Flask, request

app = Flask(__name__)
api = Api(app)

@app.route('/<path:path>')
def staticHost(self, path):
    try:
        return flask.send_from_directory(app.config['RESULT_STATIC_PATH'], path)
    except werkzeug.exceptions.NotFound as e:
        if path.endswith("/"):
            return flask.send_from_directory(app.config['RESULT_STATIC_PATH'], path + "index.html")
        raise e
