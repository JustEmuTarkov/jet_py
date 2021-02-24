from typing import ClassVar

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates

from server.app import app
from server.package_lib import PackageBase, PackageMeta


sub_api = FastAPI()


@sub_api.get("/")
def index(request: Request) -> Response:
    return Package.jinja_templates.TemplateResponse("index.html", context={"request": request})


class Package(PackageBase):
    jinja_templates: ClassVar[Jinja2Templates]

    class Meta(PackageMeta):
        name: str = "Example Mod"
        version: str = "0.0.1"

    def on_load(self) -> None:
        # Any of the tarkov package internals can be manipulated from here
        print("Example mod on_load")
        print("Visit https://127.0.0.1:443/examplemod to see index page")
        app.mount("/examplemod", sub_api)
        Package.jinja_templates = Jinja2Templates(directory=str(self.path.joinpath("templates")))
