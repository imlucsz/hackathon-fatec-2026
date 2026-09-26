from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import schemas_models as sm
import ff_router

sm.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(ff_router.router)