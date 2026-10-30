from contextlib import asynccontextmanager
import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles


from app.config import BASE_DIR, UPLOAD_DIR
from app.database import Base, engine
from app.dependencies import require_session
from app.routers import auth, employees, api_employees


# filename="app.log",      # 指定日志文件的保存路径和文件名（比如保存在当前目录的 app.log）
# encoding="utf-8"         # 设置编码，防止中文乱码
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ========== 启动阶段 ==========
    print("FastAPI 启动中...")
    # 创建上传目录
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print("engine =", engine)
    print("type =", type(engine))
    # 创建数据库表
    Base.metadata.create_all(engine)
    print("初始化完成！")
    # ========== 应用运行阶段 ==========
    yield
    # ========== 关闭阶段 ==========
    print("FastAPI 正在关闭...")
    # 释放数据库连接池
    engine.dispose()
    print("资源清理完成！")


app = FastAPI(title="社員管理システム", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR/"app/static"), name="static")


@app.get("/")
def index():
    return RedirectResponse("/login", status_code=303)


app.include_router(auth.router)
app.include_router(employees.router)
# app.include_router(api_employees.router)


@app.get("/uploads/{filename}", include_in_schema=False)
def uploaded_photo(filename: str, session=Depends(require_session)):
    path = (UPLOAD_DIR / filename).resolve()
    if path.parent != UPLOAD_DIR or not path.is_file():
        raise HTTPException(404, "画像が見つかりません。")
    return FileResponse(path, headers={"X-Content-Type-Options": "nosniff"})
