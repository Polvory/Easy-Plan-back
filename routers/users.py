from fastapi import APIRouter, HTTPException, status, Depends,Request
from typing import List
from models import User
from db import SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from schemas import TransactionResponse, CategoriesResponse, UserResponse, UserCreate  # В зависимости от структуры проекта
from auth.auth import login, guard_role, TokenPayload
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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





@router.post(
    "/init/apple/{apple_id}",
    summary="Создать нового пользователя если его нет и возврашает пользователя если он есть",
)
def init_user(apple_id: str, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.apple_id == apple_id).first()
    if existing_user:
        print('Возврщаем пользователя')
        payload:TokenPayload = {
                 "user_id": existing_user.id,
                 "role": existing_user.role,
                 "language": existing_user.language,
            }
        logger.info(f"Создан новый пользователь: {payload}")
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
    






       