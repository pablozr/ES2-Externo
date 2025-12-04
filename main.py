import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from functions.database.asyncpg_manager import asyncpg_manager
from routes.email.router import router as email_router
from routes.cartao.router import router as cartao_router
from routes.cobranca.router import router as cobranca_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncpg_manager.connect()
    yield
    await asyncpg_manager.disconnect()
app = FastAPI(lifespan=lifespan)
load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(email_router)
app.include_router(cartao_router)
app.include_router(cobranca_router)


if __name__ == '__main__':
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host='0.0.0.0', port=port)
