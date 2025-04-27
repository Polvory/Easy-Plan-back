from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List
from models import CurrencyEnum, User, Transactions  # Добавляем импорт модели Transaction
from db import SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional
from enum import Enum
from schemas import TransactionsCategoriesEnum

# Создаём роутер для пользователей
router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],  # Группировка в Swagger UI
)


# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TransactionResponse(BaseModel):
    id: int
    sum: int  # Было amount, должно быть sum
    currency: str  # Добавляем валюту
    type: str  # Добавляем тип транзакции
    user_id: int
    created_at: datetime  # Было date, должно быть created_at
    updated_at: datetime  # Добавляем обновленную дату

    class Config:
        orm_mode = True


@router.get("/all", response_model=List[TransactionResponse], summary="Получить транзакции с пагинацией")
async def get_all_transactions(
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None, description="Фильтр по ID пользователя"),
    limit: int = Query(100, gt=0, le=1000, description="Лимит количества записей (1-1000)"),
    offset: int = Query(0, ge=0, description="Смещение (количество записей для пропуска)"),
    order_by: str = Query("desc", description="Порядок сортировки по дате (asc/desc)")
):
    """
    Получает список транзакций с возможностью фильтрации и пагинации.
    
    Параметры:
    - user_id: фильтр по ID пользователя (опционально)
    - limit: количество возвращаемых записей (по умолчанию 100)
    - offset: смещение (по умолчанию 0)
    - order_by: порядок сортировки ('asc' или 'desc')
    """
    query = db.query(Transactions)
    
    if user_id is not None:
        query = query.filter(Transactions.user_id == user_id)
    
    if order_by == "asc":
        query = query.order_by(Transactions.created_at.asc())
    else:
        query = query.order_by(Transactions.created_at.desc())
    
    transactions = query.offset(offset).limit(limit).all()
    return transactions

# Перечисление типов транзакций для Pydantic модели
class TransactionTypeEnum(str, Enum):
    receipts = 'receipts'
    expenses = 'expenses'

# Модель запроса для создания транзакции
class TransactionCreateRequest(BaseModel):
    sum: int
    currency: CurrencyEnum
    type: TransactionTypeEnum  # Используем Enum для типа
    user_id: int

    @validator('sum')
    def validate_sum(cls, v, values):
        """
        Валидация суммы в зависимости от типа транзакции:
        - Для receipts (поступлений) сумма может быть любой (положительной или отрицательной)
        - Для expenses (расходов) сумма должна быть положительной
        """
        if 'type' in values and values['type'] == TransactionTypeEnum.expenses and v <= 0:
            raise ValueError('Для расходов сумма должна быть положительной')
        return v

# Модель ответа для созданной транзакции
class TransactionCreateResponse(BaseModel):
    id: int
    sum: int
    currency: str
    type: str  # Тип транзакции (receipts/expenses)
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

@router.post(
    "/",
    response_model=TransactionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую транзакцию",
    description="""
    Создаёт новую транзакцию с указанными параметрами.
    
    Особенности:
    - Для типа 'receipts' сумма может быть любой (положительной или отрицательной)
    - Для типа 'expenses' сумма должна быть строго положительной
    - Автоматически проставляется дата создания (created_at)
    """
)
async def create_transaction(
    transaction_data: TransactionCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Создание новой транзакции в системе.
    
    Параметры:
    - transaction_data: Данные для создания транзакции (сумма, валюта, тип, user_id)
    - db: Сессия базы данных (автоматически внедряется через Depends)
    
    Возвращает:
    - Созданную транзакцию с присвоенным ID и датой создания
    
    Возможные ошибки:
    - 404: Если пользователь не найден
    - 400: Если данные не прошли валидацию
    - 500: При внутренних ошибках сервера
    """
    # Проверяем существование пользователя
    user = db.query(User).filter(User.id == transaction_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    # Создаем объект транзакции
    new_transaction = Transactions(
        sum=transaction_data.sum,
        currency=transaction_data.currency,
        type=transaction_data.type,  # Используем Enum значение
        user_id=transaction_data.user_id
    )

    try:
        # Сохраняем транзакцию в базе
        db.add(new_transaction)
        db.commit()
        # Обновляем объект чтобы получить сгенерированные поля (id, created_at)
        db.refresh(new_transaction)
    except Exception as e:
        # В случае ошибки откатываем транзакцию
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании транзакции: {str(e)}"
        )

    return new_transaction