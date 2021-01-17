from mods.core.routes import (
    friend,
    hideout,
    lang,
    notifier,
    profile,
    single_player,
    trader,
    misc,
    flea_market,
    insurance,
    match,
    launcher,
)
from server import app, logger
from server.package_lib import PackageMeta, PackageBase


class Package(PackageBase):
    class Meta(PackageMeta):
        name = 'Tarkov core'
        version = '0.0.1'

    def __init__(self):
        super().__init__()
        logger.info('Tarkov core package is loading')

    def on_load(self):
        logger.info('Tarkov core package on_load was called')
        app.register_blueprint(blueprint=friend.blueprint)
        app.register_blueprint(blueprint=hideout.blueprint)
        app.register_blueprint(blueprint=lang.blueprint)
        app.register_blueprint(blueprint=notifier.blueprint)
        app.register_blueprint(blueprint=profile.blueprint)
        app.register_blueprint(blueprint=single_player.blueprint)
        app.register_blueprint(blueprint=trader.blueprint)
        app.register_blueprint(blueprint=misc.blueprint)
        app.register_blueprint(blueprint=flea_market.blueprint)
        app.register_blueprint(blueprint=insurance.blueprint)
        app.register_blueprint(blueprint=match.blueprint)
        app.register_blueprint(blueprint=launcher.blueprint)
