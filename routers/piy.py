from collections import defaultdict
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Body, HTTPException, status, Depends, Query
import logging
from auth.auth import guard_role, TokenPayload
from db import SessionLocal
from sqlalchemy.orm import Session
from enums import TransactionsTypeEnum
from models import Transactions, User
import calendar
from typing import List, Dict
from collections import defaultdict
from schemas import TransactionResponse


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/piy",
    tags=["piy"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_piy_data(operations):
    """
    Функция для получения данных для пирога.
    Возвращает словарь с данными для пирога.
    """
    # Здесь должна быть логика получения данных для пирога
    # Например, можно использовать запрос к базе данных
    # или другие источники данных
    result = []
    grouped = defaultdict(lambda: {"value": 0, "color": "", "name": ""})

    for op in operations:  # operations — твой исходный массив
        if op.debt:
            key = f'debt_{op.debt.id}'
            grouped[key]["value"] += op.sum
            grouped[key]["color"] = "#C141CC"
            grouped[key]["name"] = op.debt.name

        elif op.target:
            key = f'target_{op.target.id}'
            grouped[key]["value"] += op.sum
            grouped[key]["color"] = "#BECFDC"
            grouped[key]["name"] = op.target.name

        elif op.category:
            key = f'category_{op.category.id}'
            grouped[key]["value"] += op.sum
            grouped[key]["color"] = op.category.color
            grouped[key]["name"] = op.category.name
        else:
            # Если не задана ни цель, ни долг, ни категория
            key = f'uncategorized'
            grouped[key]["value"] += op.sum
            grouped[key]["color"] = "#B0B0B0"  # серый цвет
            grouped[key]["name"] = "Без категории"

        # Преобразуем словарь в нужный формат
    result = [{"value": v["value"], "color": v["color"], "name": v["name"]} for v in grouped.values()]
    return result 



@router.get("/piy", 
            #  response_model=List[TransactionResponse],
             summary="Собрать данные для пирога",
             status_code=status.HTTP_200_OK)
def get_piy(
    db: Session = Depends(get_db),
    date_from: Optional[date] = Query(None, description="Начальная дата фильтрации (в формате YYYY-MM-DD)", example="2025-05-01"),
    date_to: Optional[date] = Query(None, description="Конечная дата фильтрации (в формате YYYY-MM-DD)", example="2025-05-30"),
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    moded: TransactionsTypeEnum = Query(None, description="Тип операции income/expense", example="income"),
    account_id: int = Query(None, description="id счета", example=1),
    
    
):
    """
    Получает список транзакций для пирога.
        
    Параметры:
    - date_to: фильтрация по дате (конец периода)
    - date_from: фильтрация по дате (начало периода)
    - moded: тип операции income/expense
    - account_id: id счета
    """
    logger.info(f"Получает список транзакций user_id: {current_user.user_id}")
    user = db.query(User).filter(User.id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
     # Базовый запрос
    query = db.query(Transactions).filter(Transactions.user_id == user.id)
        # Применяем фильтры
    if date_from:
        query = query.filter(Transactions.created_at >= date_from)
    if date_to:
        query = query.filter(Transactions.created_at <= date_to)
    if moded:
        query = query.filter(Transactions.moded == moded)
    if account_id:
        query = query.filter(Transactions.account_id == account_id)
        # Получаем общее количество записей (без пагинации)
    transactions = query.all()   
        
    return get_piy_data(transactions)