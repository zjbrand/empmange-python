
from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.models import User, WebSession
from app.database import get_db
from app.dependencies import require_session
from app.schemas import EmployeeInput
from app.security import check_csrf
from app.services import employees
from app.views import render

router = APIRouter(tags=["社員画面"])


def parse_filters(values):
    result = {"name": values.get("searchName", "")}
    # 元组解包（Tuple Unpacking）第一次循环：source = "lowSalary" target = "salary_min"
    # 第二次循环：source = "topSalary" target = "salary_max"
    for source, target in [("lowSalary", "salary_min"), ("topSalary", "salary_max")]:
        text = str(values.get(source, "")).strip()
        # 将工资字符串转换成十进制数字
        value = Decimal(text) if text else None
        # .is_finite()用于排除 Infinity 和 NaN 这样的特殊数值
        if value is not None and (not value.is_finite() or value < 0):
            raise ValueError('給料は0以上の有限な数値にしてください。')
        # result辞書にキーと値を追加します。
        result[target] = value
    for source, target in [("dateBegin", "date_begin"), ("dateEnd", "date_end")]:
        text = str(values.get(source, "")).strip()
        result[target] = date.fromisoformat(
            text.replace("/", "-")) if text else None

    for low, high in [("salary_min", "salary_max"), ("date_begin", "date_end")]:
        if result[low] is not None and result[high] is not None and result[low] > result[high]:
            raise ValueError("検索範囲の開始値は終了値以下にしてください。")
    return result


def list_page(request: Request, db: Session, session: WebSession, filters):
    try:
        item = employees.lists(db, **parse_filters(filters))
        return render(request, "emplist.html", db, session, employees=item, filters=filters)
        # ValueError：日期格式错误、搜索范围颠倒等。InvalidOperation：Decimal() 转换非法数值时可能产生的异常。
    except (ValueError, InvalidOperation):
        return render(request, "emplist.html", db, session, status_code=400,
                      employees=[], filters=filters, error="検索条件を確認してください。日付はYYYY-MM-DD、給料は0以上、範囲は開始≦終了です。")


@router.get("/employee/lists")
@router.get("/emplist")
@router.get("/employee/search")
def lists(request: Request, db=Depends(get_db), session=Depends(require_session)):
    return list_page(request, db, session, dict(request.query_params))


@router.get("/addEmp")
def add_page(request: Request, db=Depends(get_db), session=Depends(require_session)):
    return render(request, "addEmp.html", db, session, values={})


@router.get("/employee/detail")
def detail(request: Request, id: int, db=Depends(get_db), session=Depends(require_session)):
    employee = employees.find(db, id)
    return render(request, "updateEmp.html", db, session, employee=employee,
                  values={"name": employee.name, "salary": employee.salary, "birthday": employee.birthday.isoformat()})

# employee_id=None 的作用默认参数让同一个函数可以处理两种业务：employee_id=None：新增员工，employee_id=5：修改 ID 为 5 的员工


def submit(request, db, session, name, salary, birthday, img, employee_id=None):
    employee = employees.find(
        db, employee_id) if employee_id is not None else None
    try:
        data = EmployeeInput(name=name, salary=salary, birthday=birthday)
        employees.save(db, data, img, employee_id)
    except (ValueError, ValidationError) as exc:
        error = "名前、給料（0以上・小数2桁まで）、正しい誕生日を入力してください。" if isinstance(
            exc, ValidationError) else str(exc)
        return render(request, "updateEmp.html" if employee else "addEmp.html", db, session,
                      status_code=400, employee=employee, values=dict(name=name, salary=salary, birthday=birthday.replace("/", "-")), error=error)
    return RedirectResponse("/employee/lists", status_code=303)


@router.post("/employee/save")
def save(request: Request, name: str = Form(""), salary: str = Form(""), birthday: str = Form(""),
         img: UploadFile | None = File(None), csrf_token: str = Form(""), db=Depends(get_db), session=Depends(require_session)):
    check_csrf(session, csrf_token)
    return submit(request, db, session, name, salary, birthday, img)


@router.post("/employee/update")
def update(request: Request, id: int = Form(...), name: str = Form(""), salary: str = Form(""), birthday: str = Form(""),
           img: UploadFile | None = File(None), csrf_token: str = Form(""), db=Depends(get_db), session=Depends(require_session)):
    check_csrf(session, csrf_token)
    return submit(request, db, session, name, salary, birthday, img, id)


@router.post("/employee/delete")
def delete(id: int = Form(...), csrf_token: str = Form(""), db=Depends(get_db), session=Depends(require_session)):
    check_csrf(session, csrf_token)
    employees.delete(db, id)
    return RedirectResponse("/employee/lists", status_code=303)
