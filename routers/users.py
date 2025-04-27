from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models import User
from db import SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from schemas import TransactionResponse  # В зависимости от структуры проекта
# Создаём роутер для пользователей
router = APIRouter(
    prefix="/users",
    tags=["users"],  # Группировка в Swagger UI
)

class UserResponse(BaseModel):
    id: int
    apple_id: str
    tg_id: Optional[str] = None
    tg_name: Optional[str] = None
    premium: bool = False
    premium_start: Optional[datetime] = None
    premium_expiration: Optional[datetime] = None
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    transactions: List[TransactionResponse]  # Добавляем список транзакций

class UserCreate(BaseModel):
    apple_id: str
    tg_id: Optional[str] = None
    tg_name: Optional[str] = None
    premium: Optional[bool] = False
    email: Optional[str] = None


# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/all", response_model=List[UserResponse], summary="Получить всех пользователей")
async def get_all_users(db: Session = Depends(get_db)):
    """
    Получить список всех пользователей из базы данных.
    Возвращает:
        List[UserResponse]: Список всех пользователей
    """
    try:
        users = db.query(User).all()
        # Для каждого пользователя загружаем транзакции
        for user in users:
            db.refresh(user)  # Обновляем объект
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
        return existing_user
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

            return new_user
        except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Ошибка при создании пользователя: {str(e)}"
                )
    






       