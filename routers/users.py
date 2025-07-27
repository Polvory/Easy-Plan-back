import json
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, List

from fastapi.encoders import jsonable_encoder
from jose import JWTError
from enums import CategoriTypeEnum, LanguageTypeEnum
from models import Transactions, User, Accounts
from db import SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, datetime, timedelta
from typing import Optional
from routers.limite_pyment import create_limits, delete_limit, update_limits
from schemas import RefreshTokenRequest, TransactionResponse, CategoriesResponse, UserFinance, UserResponse, UserCreate  # В зависимости от структуры проекта
from auth.auth import ALGORITHM, REFRESH_SECRET_KEY, TokenPair, login, guard_role, TokenPayload, refresh_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import contains_eager, joinedload
from sqlalchemy import and_
from passlib.hash import pbkdf2_sha256
from sqlalchemy import and_, cast, Date
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
HASH_PASWORD = "$pbkdf2-sha256$29000$.r.3VgphrJWyNsb4XytFyA$2iDszlx1jRAKXS.DUwKFR3EmoavfjmwrEmWGbCk2Hmc"


class UserOut(BaseModel):
    id: int
    apple_id: str
    role: CategoriTypeEnum
    language: LanguageTypeEnum
    payment_expires_at: Optional[datetime] = None
    payment_starts_at: Optional[datetime] = None
    payment_is_active: Optional[bool] = None
    premium: Optional[bool] = None
    premium_type: Optional[str] = None
    email: Optional[str] = None
    tg_name: Optional[str] = None
    class Config:
        from_attributes = True  # Важно для поддержки SQLAlchemy моделей
# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def loggger_json(data):
    """
    Функция для логирования данных в формате JSON.
    """
    try:
        data_dict = jsonable_encoder(data)
        data_json = json.dumps(data_dict, ensure_ascii=False, indent=2)
        logger.info(f"создаем новую транзакцию на основе текущей операции:\n{data_json}")
        return data_json
    except TypeError as e:
        logger.error(f"Ошибка при преобразовании данных в JSON: {e}")

# @router.get("/admin-only")
# async def admin_route(current_user: TokenPayload = Depends(guard_role(["admin"]))):
#     return {"message": f"Привет, {current_user.user_id}. У тебя есть права администратора."}

# @router.get("/user-and-admin-only")
# async def user_route(current_user: TokenPayload = Depends(guard_role(["user", "admin"]))):
#     return {"message": f"Привет, {current_user.user_id}. Ты обычный пользователь."}

@router.get("/all", 
           
            
            summary="Получить всех пользователей (admin)")

async def get_all_users(
    password: str = Query('AswGHT123', description="Пароль администратора", example="AswGHT123"),
    db: Session = Depends(get_db)):
    """
    Доступен только для администратора.
    Получить список всех пользователей из базы данных.
    Возвращает:
        List[UserResponse]: Список всех пользователей
    """
    try:
        is_valid = pbkdf2_sha256.verify(password, HASH_PASWORD) 
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Неверный пароль администратора"
            )
        users = db.query(User).all()
        # Для каждого пользователя загружаем транзакции
        for user in users:
            db.refresh(user)  # Обновляем объект
            # user.user_categories  # Загружаем транзакции (если используется lazy loading)
            # user.transactions  # Загружаем транзакции (если используется lazy loading)
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
    account_id: int = Query(None, description="ID счета", example=1),
    current_user: TokenPayload = Depends(guard_role(["user", "admin"])),
    db: Session = Depends(get_db)
):
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id не указан")

    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    if today.month == 12:
        next_month_start = date(today.year + 1, 1, 1)
    else:
        next_month_start = date(today.year, today.month + 1, 1)

    user = (
        db.query(User)
        .options(joinedload(User.transactions))
        .filter(User.id == current_user.user_id)
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    account = db.query(Accounts).filter(Accounts.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Счёт не найден")

    filtered_by_account = [
        t for t in user.transactions
        if t.account_id == account_id and start_of_month <= t.created_at.date() < next_month_start
    ]

    income_sum = sum(t.sum for t in filtered_by_account if t.moded == 'income')
    expense_sum = sum(t.sum for t in filtered_by_account if t.moded == 'expense')

    return {
        "balance": account.balance,
        "income": income_sum,
        "expense": expense_sum
    }



@router.put("/update",
            response_model=UserOut,
            summary="Обновить данные пользователя (user, admin)",
            description="Обновляет данные пользователя, такие как email, язык и имя в Telegram. Доступно для ролей 'user' и 'admin'."
            )
def update_user(
    current_user: TokenPayload = Depends(guard_role(["user", "admin"])),
    db: Session = Depends(get_db),
    email: Optional[str] = Query(None, description="Email пользователя", example="pol.vory@yndex.ru"),
    language: Optional[LanguageTypeEnum] = Query(None, description="Язык пользователя", example=LanguageTypeEnum.ru),
    tg_name: Optional[str] = Query(None, description="Имя пользователя в Telegram", example="@pol_vory"),
):
    try:
        user_id = current_user.user_id
        if not user_id:
            raise HTTPException(status_code=400, detail="Пользователь не найден")
        user = db.query(User).filter(User.id == user_id).first()
        if email:
            user.email = email
        if language:    
            user.language = language
        if tg_name:
            user.tg_name = tg_name
        user.updated_at = datetime.utcnow()  # Обновляем время изменения
        db.commit()
        db.refresh(user)
        return user

    except Exception as e:
        db.rollback() 
        logger.error(f"Ошибка при обновлении пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении пользователя: {str(e)}"
        )                  

@router.post("/add/paymentById", summary="Ручка добавления оплаты подписки по ID")
def add_payment_by_id(
    user_id: int = Query(..., description="ID пользователя", example=1),
    payment_profile_id: str = Query(None, description="ID в payment", example=1),
    payment_customer_user_id: str = Query(None, description="ID в payment (Незнаю зачем возможно стоит убрать)", example=1),
    payment_is_active: bool = Query(None, description="Активна ли в payment", example=True),
    payment_starts_at: datetime = Query(None, description="Дата начала подписки", example='2025-06-19T10:00:00Z'),
    payment_expires_at: datetime = Query(None, description="Дата конца подписки", example='2025-07-19T10:00:00Z'),
    premium_type:str = Query(None, description="Тип подписки", example='Pro'),
    password: str = Query('AswGHT123', description="Пароль администратора", example="AswGHT123"),
    db: Session = Depends(get_db),
):
    

    # hashed_password = pbkdf2_sha256.hash(password)
    is_valid = pbkdf2_sha256.verify(password, HASH_PASWORD) 
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный пароль администратора"
        )
    # Находим юзера
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.payment_customer_user_id = payment_customer_user_id
    user.payment_profile_id = payment_profile_id
    user.payment_is_active = payment_is_active
    user.payment_starts_at = payment_starts_at
    user.payment_expires_at = payment_expires_at
    user.premium_type = premium_type
    user.premium = True if payment_is_active else False
    
    update_limits(db, user_id, premium_type="Pro")  # Создаем лимиты для нового пользователя
    
    # Обновляем пользователя в базе данных
    try:
        db.commit()
        db.refresh(user)
        return {
            "message": "Подписка пользователя успешно обновлена",
            "user": UserOut.model_validate(user)
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при обновлении пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении пользователя: {str(e)}"
        )
    

@router.delete("/delete/paymentById", summary="Удалить подписку пользователя по ID")
def delete_payment_by_id(
    user_id: int = Query(..., description="ID пользователя", example=1),
    password: str = Query('AswGHT123', description="Пароль администратора", example="AswGHT123"),
    db: Session = Depends(get_db),
):
    is_valid = pbkdf2_sha256.verify(password, HASH_PASWORD) 
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный пароль администратора"
        )
        
    # Находим юзера
    user = db.query(User).options(joinedload(User.feature_limits)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Сбрасываем платежные данные
    user.payment_customer_user_id = None
    user.payment_profile_id = None
    user.payment_is_active = False
    user.payment_starts_at = None
    user.payment_expires_at = None
    user.premium_type = None
    user.premium = False
    
    # Сбрасываем лимиты (если они существуют)
    limits_deleted = False
    if user.feature_limits:
        limits_deleted = delete_limit(db, user.feature_limits.id)
    
    try:
        db.commit()
        db.refresh(user)
        return {
            "success": True,
            "message": "Подписка пользователя успешно удалена. Все платежные данные сброшены.",
            "details": {
                "payment_data_reset": True,
                "limits_reset": limits_deleted,
                "premium_status": False
            },
            "user": UserOut.model_validate(user)
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при обновлении пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": f"Ошибка при удалении подписки: {str(e)}",
                "details": {
                    "payment_data_reset": False,
                    "limits_reset": False
                }
            }
        )


@router.post('/add/payment',
             summary="Ручка добавления оплаты подписки"
)
def add_payment(
    payment_profile_id: str = Query(None, description="ID в payment", example=1),
    payment_customer_user_id: str = Query(None, description="ID в payment (Незнаю зачем возможно стоит убрать)", example=1),
    payment_is_active: bool = Query(None, description="Активна ли в payment", example=True),
    payment_starts_at: datetime = Query(None, description="Дата начала подписки", example='2025-06-19T10:00:00Z'),
    payment_expires_at: datetime = Query(None, description="Дата конца подписки", example='2025-07-19T10:00:00Z'),
    premium_type:str = Query(None, description="Тип подписки", example='Pro'),
    current_user: TokenPayload = Depends(guard_role(["user", "admin"])),
    db: Session = Depends(get_db),
):
    
    user_id = current_user.user_id
    # Находим юзера
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user.payment_customer_user_id = payment_customer_user_id
    user.payment_profile_id = payment_profile_id
    user.payment_is_active = payment_is_active
    user.payment_starts_at = payment_starts_at
    user.payment_expires_at = payment_expires_at
    user.premium_type = premium_type
    user.premium = True if payment_is_active else False
    
    update_limits(db, user_id, premium_type="Pro")  # Создаем лимиты для нового пользователя
    
    # Обновляем пользователя в базе данных
    try:
        db.commit()
        db.refresh(user)
        return {
            "message": "Подписка пользователя успешно обновлена",
            "user": UserOut.model_validate(user)
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при обновлении пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении пользователя: {str(e)}"
        )
 

@router.post(
    "/init/apple/{apple_id}",
    summary="Создать нового пользователя если его нет и возвратить пользователя если он есть",
)
def init_user(apple_id: str, db: Session = Depends(get_db)) -> Dict:
    # Проверка на существующего пользователя
    existing_user = db.query(User).filter(User.apple_id == apple_id).first()
    if existing_user:
        logger.info("Возвращаем пользователя")
        payload = TokenPayload(
            user_id=existing_user.id,
            role=existing_user.role,
            language=existing_user.language
        )
        token = login(payload)
        return {
            "new_user": False,
            "tokens": token,
            "user": UserOut.model_validate(existing_user),
        }

    # Создание нового пользователя
    logger.info("Создаем нового пользователя")
    new_user = User(
        apple_id=apple_id,
        role=CategoriTypeEnum.user,           # Значение по умолчанию
        language=LanguageTypeEnum.ru          # Значение по умолчанию
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        # db.flush()  # чтобы получить new_user.id
        create_limits(db, new_user.id, premium_type="basic")  # Создаем лимиты для нового пользователя
        
        payload = TokenPayload(
            user_id=new_user.id,
            role=new_user.role,
            language=new_user.language
        )
        token = login(payload)

        return {
            "new_user": True,
            "tokens": token,
            "user":  UserOut.model_validate(new_user),
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при создании пользователя: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании пользователя: {str(e)}"
        )
                
                

@router.put("/remove_payment", summary="Сбросить подписку у пользователей с истёкшей датой")
def remove_payment(db: Session = Depends(get_db)):
    today = date.today()  # Сегодняшняя дата (без времени)
    print("Запушен сброс продписки")
    # Находим пользователей, у которых:
    # 1. subscription_date < сегодня
    # 2. payment_is_active == True
    expired_subscriptions = db.query(User).filter(User.payment_expires_at <= today, User.payment_is_active == True).all()
    print(expired_subscriptions)
    if len(expired_subscriptions) > 0:
        print("Есть данные")
        for user in expired_subscriptions:
            print(f"Сбрасываем подписку у юзера ${user.id}")
            user.payment_customer_user_id = None
            user.payment_profile_id = None
            user.payment_is_active = False
            user.payment_starts_at = None
            user.payment_expires_at = None
            user.premium_type = None
            user.premium = False
            limits_deleted = False
            if user.feature_limits:
                limits_deleted = delete_limit(db, user.feature_limits.id)
            db.commit()
            db.refresh(user)
            print({
                "success": True,
                "message": "Подписка пользователя успешно удалена. Все платежные данные сброшены.",
                "details": {
                    "payment_data_reset": True,
                    "limits_reset": limits_deleted,
                    "premium_status": False
                },
                "user": UserOut.model_validate(user)
            })
    else:
        print("Пользователи не найдены")
    return expired_subscriptions
    
    

    
@router.post("/refresh", response_model=TokenPair, summary="Обновить токены пользователя")
def user_refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    return refresh_token(request, db)





       