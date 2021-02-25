from server.package_lib import PackageBase, PackageMeta
from tarkov.hideout import repositories as hideout_repositories


def set_production_time_to_1() -> None:
    for production in hideout_repositories.production_repository.production:
        production.productionTime = 1


class Package(PackageBase):
    class Meta(PackageMeta):
        name: str = "Example Mod"
        version: str = "0.0.1"

    def on_load(self) -> None:
        # Any of the tarkov package internals can be manipulated from here
        print("Example mod on_load")
        set_production_time_to_1()
