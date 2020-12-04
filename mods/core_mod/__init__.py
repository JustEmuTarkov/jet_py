from core.main import package_manager
from core.package_lib import PackageMeta, BasePackage


@package_manager.register
class Package(BasePackage):
    class Meta(PackageMeta):
        name = 'core'
        version = '0.0.1'
        dependencies = []

    def on_load(self):
        print(f'Called {self.Meta.name} on_load')
