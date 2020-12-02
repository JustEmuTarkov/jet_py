from core.app import app


@app.route('/')
def index():
    return 'Index'
