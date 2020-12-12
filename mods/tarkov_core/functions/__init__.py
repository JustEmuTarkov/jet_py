from mods.tarkov_core.functions.hideout import Hideout
from mods.tarkov_core.functions.profile import Profile


profiles = Profile()
hideout = Hideout()


def init():
    global profiles, hideout
    # im not sure how to load this shit ...
    profiles = Profile()
    hideout = Hideout()
