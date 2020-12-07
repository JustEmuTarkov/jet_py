from core.logger import logger


def init():
    import mods.tarkov_core.routes.friend
    import mods.tarkov_core.routes.hideout
    import mods.tarkov_core.routes.lang
    import mods.tarkov_core.routes.notifier
    import mods.tarkov_core.routes.profile
    import mods.tarkov_core.routes.single_player
    import mods.tarkov_core.routes.trader
