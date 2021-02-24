from fastapi import FastAPI
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from server.app import app, package_manager
from server.package_lib import PackageBase, PackageMeta


sub_api = FastAPI()
jinja_templates = Jinja2Templates(str(package_manager.packages_dir.joinpath("examplemod", "templates").absolute()))


@sub_api.get('/')
def index(request: Request):
    return jinja_templates.TemplateResponse("index.html", context={"request": request })


class Package(PackageBase):
    class Meta(PackageMeta):
        name: str = "Example Mod"
        version: str = "0.0.1"

    def on_load(self) -> None:
        # Any of the tarkov package internals can be manipulated from here
        print("Example mod on_load")
        print("Visit https://127.0.0.1:443/examplemod to see index page")
        app.mount('/examplemod', sub_api)
