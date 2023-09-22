from flask import request
from flask import Flask

import api
from storage import storage

app = Flask(__name__)

app.register_blueprint(api.bp)


@app.route("/")
def root():
    filename = request.args.get('filename', default="compressed.tracemonkey-pldi-09.pdf", type=str)
    file_path = storage.get_path(filename)

    return "Hello from Space! 🚀" + str(file_path)
