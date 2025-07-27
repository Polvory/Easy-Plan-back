
from collections import defaultdict
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Body, HTTPException, status, Depends, Query
import logging
from auth.auth import guard_role, TokenPayload
from db import SessionLocal
from sqlalchemy.orm import Session
from models import Accounts, Debts, RepeatOperations, Targets
import calendar
from typing import List, Dict



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/balance_forecast",
    tags=["balance_forecast"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




def forecast_month_end_balances(initial_balance, incomes, expenses):
    operations = []

    # Обрабатываем доходы
    for item in incomes:
        operations.append({
            "date": item.planned_date,  # если это datetime, и ты хочешь .date(), то добавь .date()
            "sum": item.balance
        })

    # Обрабатываем расходы
    for item in expenses:
        operations.append({
            "date": item.planned_date,
            "sum": -item.balance
        })

    # # Обрабатываем долги (расход на возврат долга)
    # for item in debts:
    #     operations.append({
    #         "date": item.date_end,
    #         "sum": -item.balance
    #     })

    # # Обрабатываем цели (планируем, что к дате цели нужно изъять деньги)
    # for item in targets:
    #     operations.append({
    #         "date": item.date_end,
    #         "sum": item.balance_target
    #     })

    # Сортировка по дате
    operations.sort(key=lambda x: x["date"])

    # Подсчёт баланса по дням
    daily_balances = {}
    current_balance = initial_balance

    for op in operations:
        current_balance += op["sum"]
        daily_balances[op["date"]] = current_balance

    # Группировка по последнему дню месяца
    month_end_balances = {}
    for d in daily_balances:
        year, month = d.year, d.month
        last_day = calendar.monthrange(year, month)[1]
        last_date = date(year, month, last_day)

        if last_date not in month_end_balances or d > month_end_balances[last_date]["date"]:
            month_end_balances[last_date] = {"date": d, "balance": daily_balances[d]}

    # Сортировка по дате
    result = [{"date": str(k), "balance": v["balance"]} for k, v in sorted(month_end_balances.items())]
    return result



def parse_date(date_val):
    if isinstance(date_val, datetime):
        return date_val
    return datetime.fromisoformat(date_val)

def build_forecast(data) -> List[Dict]:
    initial_balance = data["initial_balance"]
    balance = initial_balance
    events = []

    # Добавляем операции (доходы/расходы)
    for op in data["operations"]:
        events.append({
            "id": op.id,
            "name": op.name,
            "date": parse_date(op.planned_date),
            "balance": op.balance,
            "moded": op.moded
        })

    # Сортировка по дате (от старых к новым)
    events.sort(key=lambda x: x["date"])

    forecast = []
    for event in events:
        # Сначала применяем операцию к балансу
        if event["moded"] == "income":
            balance += event["balance"]
        else:
            balance -= event["balance"]
        
        # Затем записываем результат (уже с учётом текущей операции)
        forecast.append({
            "id": event["id"],
            "name": event["name"],
            "date": event["date"].strftime("%Y-%m-%d"),
            "balance": event["balance"],
            "moded": event["moded"],
            "balance_forecast": balance  # Баланс ПОСЛЕ операции
        })

    # Переворачиваем, чтобы сначала шли свежие даты
    return forecast[::-1]
# Сбор операций на прогноз баланса
@router.get("/operations", 
             summary="Собрать операции прогноза баланса",
             status_code=status.HTTP_201_CREATED)
def get_operations(
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    account_id: int = Query(None, description="id счета", example=1),
    date_from: Optional[datetime] = Query(None, description="Начальная дата для фильтрации (planned_date >= date_from)", example="2025-05-01"),
    date_to: Optional[datetime] = Query(None, description="Конечная дата для фильтрации (planned_date <= date_to)", example="2025-12-30"),
):
    user_id = current_user.user_id
        # Получаем  баланс счета
    accaunt = db.query(Accounts).filter(Accounts.id == account_id, Accounts.user_id == user_id).first()
    if not accaunt:
        logger.error(f"Счет не найден: {str(account_id)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка при получении счета"
        )
    initial_balance = accaunt.balance  # баланс на 1 июня 2025  
    
      
    # Получаем транзакции 
    query = db.query(RepeatOperations).filter(
        RepeatOperations.account_id == account_id,
        RepeatOperations.user_id == user_id
        # RepeatOperations.debt_id == None,
        # RepeatOperations.target_id == None,
        
    )
    if date_from:
        query = query.filter(RepeatOperations.planned_date >= date_from)
    if date_to:
        query = query.filter(RepeatOperations.planned_date <= date_to)
    operations = query.all()
    
    def get_debts():
            query = db.query(Debts).filter(
                Debts.account_id == account_id,
                Debts.user_id == user_id,
            )
            if date_from:
                query = query.filter(Debts.date_end >= date_from)
            if date_to:
                query = query.filter(Debts.date_end <= date_to)
            return query.all()


    def get_targets():
        query = db.query(Targets).filter(
            Targets.account_id == account_id,
            Targets.user_id == user_id,
        )
        if date_from:
            query = query.filter(Targets.date_end >= date_from)
        if date_to:
            query = query.filter(Targets.date_end <= date_to)
        return query.all() 
    
    debts_list = get_debts()
    targets_list = get_targets()
    # "moded": "income",
    # "name": "string",
    #  "balance": 100000,
    print('-------------')
    print(initial_balance)
    
    data = {
        "initial_balance":initial_balance,
        # "debts_list":[],
        "operations":operations,
        # "targets_list": []
            }
    forecast_data = build_forecast(data)
   
    return forecast_data[::-1]   # <-- Переворачиваем массив перед возвратом








@router.get("/generate", summary="Собрать прогноз баланса")
def generate_balance_forecast(
    db: Session = Depends(get_db),
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    account_id: int = Query(None, description="id счета", example=1),
    date_from: Optional[datetime] = Query(None, description="Начальная дата для фильтрации (planned_date >= date_from)", example="2025-05-01"),
    date_to: Optional[datetime] = Query(None, description="Конечная дата для фильтрации (planned_date <= date_to)", example="2025-12-30"),
):
    

        
    user_id = current_user.user_id
    
    try:
       
    
        # Получаем  баланс счета
        accaunt = db.query(Accounts).filter(Accounts.id == account_id, Accounts.user_id == user_id).first()
        print(accaunt)
        initial_balance = accaunt.balance  # баланс на 1 июня 2025

        def get_operations(moded_type,):
            query = db.query(RepeatOperations).filter(
                RepeatOperations.account_id == account_id,
                RepeatOperations.user_id == user_id,
                RepeatOperations.moded == moded_type
                # RepeatOperations.debt_id == None,
                # RepeatOperations.target_id == None,

            )
            if date_from:
                query = query.filter(RepeatOperations.planned_date >= date_from)
            if date_to:
                query = query.filter(RepeatOperations.planned_date <= date_to)
            return query.all()
        def get_debts():
            query = db.query(Debts).filter(
                Debts.account_id == account_id,
                Debts.user_id == user_id,
            )
            if date_from:
                query = query.filter(Debts.date_end >= date_from)
            if date_to:
                query = query.filter(Debts.date_end <= date_to)
            return query.all()


        def get_targets():
            query = db.query(Targets).filter(
                Targets.account_id == account_id,
                Targets.user_id == user_id,
            )
            if date_from:
                query = query.filter(Targets.date_end >= date_from)
            if date_to:
                query = query.filter(Targets.date_end <= date_to)
            return query.all()        
        #     date_end
        # Получаем списки операций
        incomes_list = get_operations("income")
        expenses_list = get_operations("expense")
        # debts_list = get_debts()
        # targets_list = get_targets()


        return forecast_month_end_balances(initial_balance, incomes_list, expenses_list )
    except TypeError as e:
        logger.error(f"Ошибка получения прогноза: {e}")
    # return 
    # 
 
    
    # return targets_list
    # Сгруппировать по датам с суммой
    # def group_by_date(operations):
    #     grouped = defaultdict(int)
    #     for op in operations:
    #         date = op.planned_date.date()  # только дата, без времени
    #         grouped[date] += op.balance
    #     return [{"date": str(date), "sum": amount} for date, amount in sorted(grouped.items())]


    # Для прогноза нужно привязать счет к долгу
    # Редактировать транзакцию 
    # Огрничит валюту редактирование транзакции 
    # 


    # incomes = group_by_date(incomes_list)
    # expenses = group_by_date(expenses_list)
    

    # return forecast_month_end_balances(initial_balance, incomes, expenses)

    # return {
    #     "initial_balance": initial_balance,
    #     "incomes": incomes,
    #     "expenses": expenses
    # }



