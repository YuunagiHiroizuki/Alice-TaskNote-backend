# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 使用 SQLite 数据库（无需额外安装，测试/开发首选）
SQLALCHEMY_DATABASE_URL = "sqlite:///./todo.db"

# 创建数据库引擎（SQLite 需要加 check_same_thread=False）
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基类，所有 ORM 模型继承这个类
Base = declarative_base()

# 依赖函数：每次请求创建一个数据库会话，请求结束关闭
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()