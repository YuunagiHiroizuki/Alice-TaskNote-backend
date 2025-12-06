from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import todos, notes
from .database import engine
from . import models

# 创建数据库表
models.Base.metadata.create_all(bind=engine)


app = FastAPI(title="TODO + Notes API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(todos.router)
app.include_router(notes.router)
