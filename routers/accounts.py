from fastapi import APIRouter, HTTPException, status, Depends, Query, Response
from typing import List
from models import Accounts, TransactionsTypeEnum, User, Categories  # Добавляем импорт модели Transaction
from db import SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy.orm import load_only
from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional
from schemas import AccountCreate, AccountResponse, AccountUpdate, CategoriesResponse, CreateCategori, UpdateCategoryRequest
from fastapi.responses import JSONResponse
from auth.auth import login, guard_role, TokenPayload



import logging
# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём роутер для пользователей
router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],  # Группировка в Swagger UI
)

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# Получить все аккаунты пользователя
@router.get("/",
            summary="Получить аккаунты пользователя (user/admin)",
            response_model=List[AccountResponse],
            status_code=status.HTTP_200_OK)
def get_accounts(
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db),
    archive:bool =  Query( description="Архив", example=False),
    
    ):
    try:
        logger.info(f"Получение аккаунтов для user_id: {current_user}")
        user_id = current_user.user_id
        accounts = db.query(Accounts)
        if user_id is not None:
            # Если указан user_id
            accounts = accounts.filter(Accounts.user_id == user_id)
        # .filter(Accounts.user_id == user_id).all()
        # if date_from:
            accounts = accounts.filter(Accounts.archive == archive)
        
        if not accounts:
            raise HTTPException(status_code=404, detail="No accounts found")
        return accounts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении аккаунтов: {str(e)}"
        )


# Создание нового аккаунта
@router.post("/", 
            summary="Создание нового счета (user/admin)",
            response_model=AccountResponse, 
            status_code=status.HTTP_201_CREATED)
def create_account(
    account: AccountCreate, 
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])),
    db: Session = Depends(get_db)):
    logger.info(f"Создание аккаунта для user_id: {current_user}")
    new_account = Accounts(
        name=account.name,
        currency=account.currency,
        balance=account.balance,
        archive=account.archive,
        user_id=current_user.user_id,  # Подразумеваем, что это передается в запросе
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account

# Редактирование аккаунта
@router.put("/{account_id}", 
            summary="Редактирование аккаунта (user/admin)",
            # response_model=AccountResponse,
            )
def update_account(
    account_id: int, 
    update_data: AccountUpdate,
    current_user: TokenPayload = Depends(guard_role(["admin", "user"])), 
    db: Session = Depends(get_db)):
    """
    Обновляет данные счета.
    - Можно обновлять отдельные поля (name, currency, balance, archive)
    - Возвращает обновленный счет
    """
    try:
        logger.info(f"Обновляем счет для user_id: {current_user.role} {current_user.user_id}")
        account:Accounts = db.query(Accounts).filter(Accounts.id == account_id).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Счет не найден"
            )
         # Проверка принадлежности пользователю (если передан user_id)
        if current_user.user_id is not None:
            if account.user_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Счет не принадлежит указанному пользователю"
                )
        if update_data.name is not None:
            account.name = update_data.name
        if update_data.currency is not None:
            account.currency = update_data.currency
        if update_data.balance is not None:
            account.balance = update_data.balance
        # if update_data.archive is not None:
        #     account.archive = update_data.archive
        
        db.commit()
        db.refresh(account)
        
        return account
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении счета: {str(e)}"
        )
#     db_account = db.query(Accounts).filter(Accounts.id == account_id).first()
#     if not db_account:
#         raise HTTPException(status_code=404, detail="Account not found")

#     db_account.name = account.name
#     db_account.currency = account.currency
#     db_account.balance = account.balance
#     db_account.archive = account.archive

#     db.commit()
#     db.refresh(db_account)
#     return db_account

# # Архивирование аккаунта
# @router.patch("/{account_id}/archive", response_model=AccountResponse)
# def archive_account(account_id: int, db: Session = Depends(get_db)):
#     db_account = db.query(Accounts).filter(Accounts.id == account_id).first()
#     if not db_account:
#         raise HTTPException(status_code=404, detail="Account not found")

#     db_account.archive = True
#     db.commit()
#     db.refresh(db_account)
#     return db_account

# # Деархивирование аккаунта
# @router.patch("/{account_id}/unarchive", response_model=AccountResponse)
# def unarchive_account(account_id: int, db: Session = Depends(get_db)):
#     db_account = db.query(Accounts).filter(Accounts.id == account_id).first()
#     if not db_account:
#         raise HTTPException(status_code=404, detail="Account not found")

#     db_account.archive = False
#     db.commit()
#     db.refresh(db_account)
#     return db_account