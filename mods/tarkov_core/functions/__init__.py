from mods.tarkov_core.functions.profile import Profile


profiles = {}


def init():
    global profiles
    # im not sure how to load this shit ...
    profiles = Profile()
