from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List

from jose import JWTError
from models import Transactions, User, Accounts
from db import SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, timedelta
from typing import Optional
from schemas import RefreshTokenRequest, TransactionResponse, CategoriesResponse, UserFinance, UserResponse, UserCreate  # В зависимости от структуры проекта
from auth.auth import ALGORITHM, REFRESH_SECRET_KEY, TokenPair, login, guard_role, TokenPayload, refresh_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import contains_eager, joinedload
from sqlalchemy import and_
# from guard.guard import get_current_user, TokenPayload
import logging
# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Создаём роутер для пользователей
router = APIRouter(
    prefix="/users",
    tags=["users"],  # Группировка в Swagger UI
)

security = HTTPBearer()

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# @router.get("/admin-only")
# async def admin_route(current_user: TokenPayload = Depends(guard_role(["admin"]))):
#     return {"message": f"Привет, {current_user.user_id}. У тебя есть права администратора."}

# @router.get("/user-and-admin-only")
# async def user_route(current_user: TokenPayload = Depends(guard_role(["user", "admin"]))):
#     return {"message": f"Привет, {current_user.user_id}. Ты обычный пользователь."}

@router.get("/all", 
            response_model=List[UserResponse],
            
            summary="Получить всех пользователей (admin)")

async def get_all_users(
    current_user: TokenPayload = Depends(guard_role(["admin"])),
    db: Session = Depends(get_db)):
    """
    Доступен только для администратора.
    Получить список всех пользователей из базы данных.
    Возвращает:
        List[UserResponse]: Список всех пользователей
    """
    try:
        users = db.query(User).all()
        # Для каждого пользователя загружаем транзакции
        for user in users:
            db.refresh(user)  # Обновляем объект
            user.user_categories  # Загружаем транзакции (если используется lazy loading)
            user.transactions  # Загружаем транзакции (если используется lazy loading)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении пользователей: {str(e)}"
        )


@router.get(
    '/finance',
    status_code=status.HTTP_200_OK,
    summary="Получаем финансы пользователя",
) 
def get_finance(
    account_id:int = Query(None, description="ID счета" , example=1),
    current_user: TokenPayload = Depends(guard_role(["user", "admin"])),
    db: Session = Depends(get_db)
):
    
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id не указан")
    # Текущая дата
    today = date.today()
    # Начало месяца
    start_of_month = date(today.year, today.month, 1)
    # Начало следующего месяца
    if today.month == 12:
        next_month_start = date(today.year + 1, 1, 1)
    else:
        next_month_start = date(today.year, today.month + 1, 1)

    # Конец месяца = день перед началом следующего
    end_of_month = next_month_start - timedelta(days=1)

    print("Начало месяца:", start_of_month)
    print("Конец месяца:", end_of_month)
    
    user_with_transactions = (
        db.query(User)
        .options(joinedload(User.transactions))
        .filter(User.id == current_user.user_id,
            Transactions.created_at >= start_of_month,
            Transactions.created_at < next_month_start,
            )  
        .first()
        )
    
    
    account = db.query(Accounts).filter(Accounts.id == account_id).first()


    # Фильтрация транзакций по account_id
    filtered_by_account = [
        t for t in user_with_transactions.transactions
        if t.account_id == account_id  # Фильтруем по account_id
    ]
    for t in filtered_by_account:
        print(f"ID: {t.id}, Сумма: {t.sum}, Тип: {t.moded}, Дата: {t.created_at}, ID счета: {t.account_id}, ID категории: {t.account_id}")
    
    if not user_with_transactions:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    income_sum = sum(t.sum for t in filtered_by_account if t.moded == 'income')
    expense_sum = sum(t.sum for t in filtered_by_account if t.moded == 'expense')

    return {
        "balance": account.balance,
        "income": income_sum,
        "expense": expense_sum
    }



@router.post(
    "/init/apple/{apple_id}",
    summary="Создать нового пользователя если его нет и возврашает пользователя если он есть",
)
def init_user(apple_id: str, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.apple_id == apple_id).first()
    if existing_user:
        print('Возврщаем пользователя')
        # user_actual = TokenPayload(
        #         user_id=user_in_db.id,
        #         role=user_in_db.role,
        #         language=user_in_db.language
        #     )
        payload = TokenPayload(
                 user_id=existing_user.id,
                 role=existing_user.role,
                 language=existing_user.language,
        )
        logger.info(f"Возврщаем пользователя: {payload}")
        token = login(payload)
        return {
            "new_user": False,
            "tokens":token,
            "user":existing_user,
                }
    else:
        print('Создаем нового пользователя')
    # Создаем нового пользователя с переданными данными и значениями по умолчанию
        new_user = User(
            apple_id=apple_id,
        )
        try:
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            payload:TokenPayload = {
                 "user_id": new_user.id,
                 "role": new_user.role,
                 "language": new_user.language,
            }
            logger.info(f"Создан новый пользователь: {payload}")
            token = login(payload)
            return {
                "new_user": True,
                "tokens":token,
                "user":new_user,
                }
        except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Ошибка при создании пользователя: {str(e)}"
                )
                
                


    
@router.post("/refresh", response_model=TokenPair, summary="Обновить токены пользователя")
def user_refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    return refresh_token(request, db)





       