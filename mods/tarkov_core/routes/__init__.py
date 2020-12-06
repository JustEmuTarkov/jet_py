from core.logger import logger


def init():
    logger.debug('Initializing tarkov_core  routes')
    import mods.tarkov_core.routes.hideout
    import mods.tarkov_core.routes.lang
    import mods.tarkov_core.routes.profile
