import tarkov
from tarkov.launcher.container import LauncherContainer

container = LauncherContainer()
container.wire(packages=[tarkov])
