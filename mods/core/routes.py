from core.app import app


@app.route('/', methods=["POST", "GET"])
def _index():
    return '/'
