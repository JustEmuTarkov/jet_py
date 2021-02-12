from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware

import tarkov.trader.routes

app = FastAPI()

app.include_router(router=tarkov.trader.routes.router)
app.add_middleware(GZipMiddleware, minimum_size=-1)
