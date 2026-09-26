from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import ff_router
import schemas_models as sm
from database import engine

sm.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FATEC Itaquera API",
    version="1.0.0",
    description="API de comunicação acadêmica para professores, alunos e chatbot da FATEC Itaquera.",
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "message": "Dados de entrada inválidos.",
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erro interno do servidor.",
            "message": "Ocorreu um erro inesperado. Tente novamente mais tarde.",
        },
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ff_router.router)