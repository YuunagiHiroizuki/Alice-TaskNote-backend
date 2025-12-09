# main.py - 确保正确导入路由
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import todos, notes, tags, stats 
from .database import engine
from .models import * 

Base.metadata.create_all(bind=engine) 

app = FastAPI(
    title="TODO + Notes + Stats API",
    description="任务、笔记和统计管理系统API",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://localhost:5173",  
        "https://alice-task-note.vercel.app/"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(todos.router)
app.include_router(notes.router)
app.include_router(tags.router)  
app.include_router(stats.router)  
  

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
