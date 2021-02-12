from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware

import tarkov.routes.friend
import tarkov.routes.hideout
import tarkov.trader.routes

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=-1)

app.include_router(router=tarkov.routes.friend.router)
app.include_router(router=tarkov.trader.routes.router)
app.include_router(router=tarkov.routes.hideout.router)
