from fastapi import FastAPI
from pydantic import BaseModel
from fast_api.router import routers
app = FastAPI()
  

for router in routers:
    app.include_router(router)

