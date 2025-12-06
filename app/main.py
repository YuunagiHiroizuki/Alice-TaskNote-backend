# main.py - 确保正确导入路由
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import todos, notes, stats # 导入stats
from .database import engine
from . import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TODO + Notes + Stats API",
    description="任务、笔记和统计管理系统API",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",  # 移除末尾斜杠
        "http://127.0.0.1:5174",  # 添加127.0.0.1
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(todos.router)
app.include_router(notes.router)
app.include_router(stats.router)  # 添加stats路由
  

@app.get("/")
async def root():
    return {
        "message": "TODO + Notes + Stats API Service",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "tasks": "/api/tasks",
            "notes": "/api/notes",
            "stats": "/api/stats"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

 
