import sys

from server import app, logger, root_dir
from server.package_lib import PackageManager
from tarkov import launcher, notifier
from tarkov.routes import (flea_market, friend, hideout, insurance, lang, match, misc, profile, single_player)

if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

mods_dir = root_dir.joinpath('mods')

if __name__ == '__main__':
    app.register_blueprint(blueprint=friend.blueprint)
    app.register_blueprint(blueprint=hideout.blueprint)
    app.register_blueprint(blueprint=lang.blueprint)
    app.register_blueprint(blueprint=profile.blueprint)
    app.register_blueprint(blueprint=single_player.blueprint)
    # app.register_blueprint(blueprint=trader.blueprint)
    app.register_blueprint(blueprint=misc.blueprint)
    app.register_blueprint(blueprint=flea_market.blueprint)
    app.register_blueprint(blueprint=insurance.blueprint)
    app.register_blueprint(blueprint=match.blueprint)

    app.register_blueprint(blueprint=launcher.blueprint)
    app.register_blueprint(blueprint=notifier.blueprint)

    logger.debug(f'Searching for packages in: {mods_dir}')
    package_manager = PackageManager(mods_dir)
    package_manager.load_packages()

    app.run(ssl_context='adhoc', port=443, threaded=True)
