# schemas.py
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class TransactionsTypeEnum(str, Enum):
    income = 'income'
    expense = 'expense'

class TransactionResponse(BaseModel):
    id: int
    sum: int
    currency: str
    type: str
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CategoriesResponse(BaseModel):
    id: int
    name: str  # Было amount, должно быть sum
    icon: Optional[str] = None  # Добавляем валюту
    color: str  # Добавляем тип транзакции
    svg:Optional[str] = None
    moded: str  # Добавляем тип транзакции
    type:str
    user_id: Optional[int] = None  # Может быть int или None
    created_at: datetime  # Было date, должно быть created_at
    updated_at: datetime  # Добавляем обновленную дату

    class Config:
        orm_mode = True

class CreateCategori(BaseModel):
    name: str = Field(example="Еда")
    icon: str = Field(example="🍕")
    color: str = Field(example="#FF5733")
    svg: str = Field(example="<svg>...</svg>") 
    moded: TransactionsTypeEnum  # ← теперь тип строго соответствует
    class Config:
        orm_mode = True

# Модель для обновления категории
class UpdateCategoryRequest(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    svg: Optional[str] = None
    moded: TransactionsTypeEnum  # ← теперь тип строго соответствует
    class Config:
        orm_mode = True
    


    
class TransactionsCategoriesEnum(str, Enum):
    # Поступления (receipts)
    SALARY = "Зарплата"
    BUSINESS_INCOME = "Бизнес доход"
    INVESTMENTS = "Инвестиции"
    GIFTS = "Подарки"
    REFUNDS = "Возвраты"
    OTHER_INCOME = "Другие поступления"
    
    # Расходы (expenses)
    SUPERMARKET = "Супермаркеты"
    HEALTH = "Здоровье"
    TRANSPORT = "Транспорт"
    ENTERTAINMENT = "Развлечения"
    COMMUNICATION = "Связь"
    EDUCATION = "Образование"
    RENT = "Аренда"
    UTILITIES = "Коммунальные услуги"
    RESTAURANTS = "Рестораны"
    CLOTHING = "Одежда"
    TRAVEL = "Путешествия"
    INSURANCE = "Страхование"
    TAXES = "Налоги"
    CHARITY = "Благотворительность"
    HOUSEHOLD = "Хозтовары"
    PETS = "Питомцы"
    CHILDREN = "Дети"
    BEAUTY = "Красота"
    ELECTRONICS = "Электроника"
    SUBSCRIPTIONS = "Подписки"
    OTHER_EXPENSES = "Другие расходы"
    
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
    user_categories: List[CategoriesResponse]

class UserCreate(BaseModel):
    apple_id: str
    tg_id: Optional[str] = None
    tg_name: Optional[str] = None
    premium: Optional[bool] = False
    email: Optional[str] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_data:object