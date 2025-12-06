# main.py - 确保正确导入路由
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import todos, notes, tags  
from .database import engine
from . import models

# 创建数据库表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TODO + Notes API",
    description="任务和笔记管理系统API",
    version="1.0.0"
)

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


@app.get("/")
async def root():
    return {
        "message": "TODO + Notes API Service",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "tasks": "/api/tasks",
            "notes": "/api/notes"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

app.include_router(tags.router)  

