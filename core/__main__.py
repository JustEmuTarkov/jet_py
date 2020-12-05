from core.app import app
from core.main import package_manager
import ujson
import core.utils

@app.route('/')
def index():
    return 'index'


package_manager.load_packages()
app.run()

