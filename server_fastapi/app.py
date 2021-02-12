from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware

from tarkov.routes import trader

app = FastAPI()

app.include_router(router=trader.router)
app.add_middleware(GZipMiddleware, minimum_size=-1)
