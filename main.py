from fastapi import FastAPI

from routes import routers


app = FastAPI(
    title="Free API Collection",
    description="A collection of free utility APIs.",
    version="1.0.0",
)

for router in routers:
    app.include_router(router)
