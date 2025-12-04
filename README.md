# 项目说明

Python 3.13.2
FastAPI+SQLite

## 部署

```bash
venv\Scripts\activate
```

## 安装依赖

```bash
pip install fastapi uvicorn[standard] sqlalchemy pydantic sqlite3 fastapi[all] python-multipart
```

## 启动服务

```bash
uvicorn app.main:app --reload
```

访问：

- `http://127.0.0.1:8000/docs` → Swagger UI（交互文档）

- `http://127.0.0.1:8000/redoc` → Redoc 文档

## 对接前端

前端发请求到 `http://127.0.0.1:8000/todos` 或 `/notes`

如果用 Vue、React、Vite 等，确保前端地址在 origins 中配置了 CORS

FastAPI 会自动处理 JSON 请求和响应，前端直接用 fetch 或 axios 调用即可
