from fastapi import APIRouter, HTTPException, status, Depends, Query
from db import SessionLocal
from sqlalchemy.orm import Session
from models import Accounts, Debts, Feature_limits, Limits, Targets
from sqlalchemy.exc import SQLAlchemyError
# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_limits(db: Session, user_id: int, limit_key: str = None):
    limits = db.query(Feature_limits).filter(Feature_limits.user_id == user_id).first()
    print(limit_key)
    
    if not limits:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Limits not found for user")
    if limit_key == "account_management":
        limits = getattr(limits, limit_key)
        accounts = db.query(Accounts).filter(Accounts.user_id == user_id)
        total = accounts.count()
        if total >= limits:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="предельное количество аккаунтов достигнуто, обновите подписку для увеличения лимита"
            )
    if limit_key == "debts":
        limits = getattr(limits, limit_key)
        debts = db.query(Debts).filter(Debts.user_id == user_id)
        total = debts.count()
        if total >= limits:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="предельное количество долгов достигнуто, обновите подписку для увеличения лимита"
            )
    if limit_key == "limits":
        limits = getattr(limits, limit_key)
        limits_data = db.query(Limits).filter(Limits.user_id == user_id)
        total = limits_data.count()
        if total >= limits:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="предельное количество лимитов достигнуто, обновите подписку для увеличения лимита"
            )
    if limit_key == "goals":
        limits = getattr(limits, limit_key)
        targets = db.query(Targets).filter(Targets.user_id == user_id)
        total = targets.count()
        if total >= limits:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="предельное количество целей достигнуто, обновите подписку для увеличения лимита"
            )
    if limit_key == "open_ai_balance":
        limits = getattr(limits, limit_key)
        if limits <= 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="предельное количество запрососв достигнуто, обновите подписку для увеличения лимита"
            )
    if limit_key == "open_ai_tasks":
       limits = getattr(limits, limit_key)
       if limits <= 0:
           raise HTTPException(
               status_code=status.HTTP_403_FORBIDDEN,
               detail="предельное количество запрососв достигнуто, обновите подписку для увеличения лимита"
           )
 
def subtract_open_ai_balance(db: Session, user_id: int):
    limit = db.query(Feature_limits).filter(Feature_limits.user_id == user_id).first()
    if limit.open_ai_balance > 0:
        limit.open_ai_balance = limit.open_ai_balance - 1
        db.commit()
        db.refresh(limit)
        print("Обновили лимит chat GPT")


def subtract_open_ai_tasks(db: Session, user_id: int):
    limit = db.query(Feature_limits).filter(Feature_limits.user_id == user_id).first()
    if limit.open_ai_tasks > 0:
        limit.open_ai_tasks = limit.open_ai_tasks - 1
        db.commit()
        db.refresh(limit)
        print("Обновили лимит chat GPT")
 

def update_limits(db: Session, user_id: int, premium_type: str = "basic"):
    print('Updating limits for user:', user_id, 'with premium type:', premium_type)
    limits_config = {
        "basic": {
            "account_management": 1,
            "goals": 2,
            "tasks": 3,
            "limits": 2,
            "debts": 1,
            "open_ai_balance": 3,
            "open_ai_tasks": 3
        },
        "Pro": {
            "account_management": 100,  # Или больше, если нужно
            "goals": 100,
            "tasks": 200,
            "limits": 200,
            "debts": 200,
            "open_ai_balance": 50,
            "open_ai_tasks": 50
        }
    }

    config = limits_config.get(premium_type)
    if not config:
        raise ValueError(f"Unknown premium type: {premium_type}")

    limits = db.query(Feature_limits).filter(Feature_limits.user_id == user_id).first()
    if not limits:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Limits not found for user")

    for key, value in config.items():
        setattr(limits, key, value)

    db.commit()
    db.refresh(limits)
    return limits

def delete_limit(db: Session, limit_id:int):
    try:
        limit = db.query(Feature_limits).filter(Feature_limits.id == limit_id).first()
        if not limit:
            return False
  
        limit.account_management = 1
        limit.goals = 2
        limit.tasks = 3
        limit.limits = 2
        limit.debts = 1
        limit.open_ai_balance = 3
        limit.open_ai_tasks = 3
       
        db.commit()
        db.refresh(limit)
        return True
        
    except SQLAlchemyError as e:
        db.rollback()  # Откатываем изменения при ошибке
        print(f"Error deleting limit: {e}")
        return False

def create_limits(db: Session, user_id: int, premium_type: str = "basic"):
    print('Creating limits for user:', user_id, 'with premium type:', premium_type)
    limits_config = {
        "basic": {
            "account_management": 1,
            "goals": 2,
            "tasks": 3,
            "limits": 2,
            "debts": 1,
            "open_ai_balance": 3,
            "open_ai_tasks": 3
        },
        "Pro": {
            "account_management": 100,  # Или больше, если нужно
            "goals": 100,
            "tasks": 200,
            "limits": 200,
            "debts": 200,
            "open_ai_balance": 50,
            "open_ai_tasks": 50
        }
    }

    config = limits_config.get(premium_type)
    if not config:
        raise ValueError(f"Unknown premium type: {premium_type}")

    limits = Feature_limits(
        user_id=user_id,
        subscription_type=premium_type,
        **config
    )

    db.add(limits)
    db.commit()
    db.refresh(limits)
    return limits

    # db.refresh(new_user)

    # return new_user
    # return {
    #     "account_management": 1,
    #     "planning": 2,
    #     "liabilities": 2,
    #     "task_tracker": 3,
    #     "limits": 2,
    #     "debts": 1,
    #     "open_ai_balanse": 3,
    #     "open_tsak": 3
    # }