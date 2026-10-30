# emphtml-python 员工管理教学项目

从 Spring Boot emphtml 迁移到 FastAPI，保留注册/验证码/登录/退出、员工增删改查、组合查询、照片新增与替换。保留原项目的路由名、表单字段和日文页面用语，复用原 CSS、JS 与静态图片；页面改用 Jinja2 并提取公共布局。

## 启动（Windows PowerShell，Python 3.11+）

```powershell
cd C:\Apython\emphtml-python
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 9099 --reload
```

不需要激活虚拟环境，也不需要安装 MySQL。依赖已安装时可以直接运行 python -m uvicorn app.main:app --port 9099 --reload。也可运行 `powershell -ExecutionPolicy Bypass -File .\run.ps1`，脚本优先使用本地虚拟环境。

打开 http://127.0.0.1:8000 。首次启动自动创建 `emphtml.db` 和表。没有预置账号，请点击注册，输入至少6位密码和图片验证码，再登录。原 Java 项目和数据库不会被修改，不会自动导入其账号、员工或上传文件。

## 手动走一遍

1. 注册账号（可测试错误验证码、重复用户名），再登录。
2. 新增员工，填写姓名、工资、生日，可选上传 PNG/JPEG/GIF 照片。
3. 在列表按姓名、工资上下限、生日上下限组合查询；日期支持 YYYY-MM-DD 和 YYYY/MM/DD。
4. 编辑员工：不选文件保留旧照片；选择新照片替换旧照片。
5. 删除员工：确认后删除记录及照片。
6. 安全退出，重新访问列表应跳回登录。
7. 登录状态下打开 `/docs`，尝试 `GET /api/employees`；未登录请求 API 返回401。

## 代码阅读顺序

- `app/main.py`：启动、建表、静态资源、路由注册。
- `app/database.py`、`models.py`：连接、数据库会话、表结构。
- `app/routers/employees.py`：对应 Java EmployeeController。
- `app/services/employees.py`：对应 Service 和 MyBatis 的查询/事务/照片处理。
- `app/routers/auth.py`、`services/auth.py`：对应 UserController、UserServiceImpl。
- `app/dependencies.py`、`security.py`：登录检查、会话、CSRF 和密码哈希。
- `app/schemas.py`：Pydantic 输入校验及 JSON 输出定义。
- `app/templates/`：Jinja2 替代 Thymeleaf；`base.html` 是公共布局。
- `app/routers/api_employees.py`：进阶用只读 JSON API，共用员工业务层。写入操作先通过网页表单教学。

## 与原项目的差异

- 默认 SQLite 自动建表，保留 user、employee 的业务字段；salary 为 Decimal/Numeric，birthday 为 date。
- Java Service 接口和实现类合并为业务函数；MyBatis XML 改为 SQLAlchemy 同步查询。
- 原 Session 中的 JWT 改为数据库服务端会话。Cookie 仅含随机标识，有效期2小时，登录时轮换，退出后失效；验证码也只存服务端并在校验时消耗。
- MD5 改为带随机盐的 PBKDF2-SHA256（600000次），不记录密码。原 MD5 账号不能直接用于本项目。
- 删除、退出改为 POST；修改表单有 CSRF 校验；搜索默认 GET，兼容原 POST 搜索。
- 保留 `/login`、`/register`、`/user/login`、`/user/register`、`/user/generateImageCode`、`/user/logout`、`/employee/lists`、`/employee/search`、`/addEmp`、`/employee/detail?id=...`、`/employee/save`、`/employee/update`、`/employee/delete`。
- 查询范围非法时提示；员工不存在返回404；日期/工资在服务端验证。照片使用随机文件名、真实图片校验、5MB限制，更新成功后再清理旧照片。
- 新增员工照片可不选，不选择时显示“未设置”；原项目未选择文件可能报错。

## 测试

```powershell
python -m unittest discover -s tests -v
```

测试使用临时 SQLite 和临时上传目录，不读写实际教学数据。验证码在自动化测试中从测试数据库读取，应用未提供验证码答案接口。

## 可选 MySQL

先创建独立的新数据库，不要直接指向旧项目数据库。安装驱动后通过环境变量配置：

```powershell
python -m pip install pymysql
$env:DATABASE_URL = 'mysql+pymysql://用户名:密码@127.0.0.1:3306/emphtml_python?charset=utf8mb4'
python -m uvicorn app.main:app --reload
```

`.env.example` 仅是配置示例，不自动加载。MySQL连接方式尚未实机验证。`create_all` 仅负责创建缺失表，后续修改表结构需要迁移。项目用于本地教学；验证码无障碍替代、限流、找回密码、生产部署和 Alembic 迁移尚未实现。
