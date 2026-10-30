"""进阶章节：只读 JSON API；复用网页的员工查询业务。"""
from fastapi import APIRouter, Depends
from app.database import get_db
from app.dependencies import require_api_user
from app.schemas import EmployeeRead
from app.services import employees

router = APIRouter(prefix="/api/employees", tags=["社員API"], dependencies=[Depends(require_api_user)])

@router.get("", response_model=list[EmployeeRead])
def lists(db=Depends(get_db)):
    return employees.lists(db)

@router.get("/{employee_id}", response_model=EmployeeRead)
def detail(employee_id: int, db=Depends(get_db)):
    return employees.find(db, employee_id)
