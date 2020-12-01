from core import mod_loader
from core.app import app

if __name__ == '__main__':
    mod_loader.load_mods()

    app.run()
