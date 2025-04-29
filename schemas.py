# schemas.py
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

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
    icon: str  # Добавляем валюту
    color: str  # Добавляем тип транзакции
    svg:str
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
    type: str = Field(example="admin")
    user_id: Optional[int] = Field(None, example=1)  # None по умолчанию, пример: 1
    

    class Config:
        orm_mode = True

# Модель для обновления категории
class UpdateCategoryRequest(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    svg: Optional[str] = None
    user_id: Optional[int] = None
    
# Модель для обновления админской категории
class UpdateAdminCategoryRequest(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    svg: Optional[str] = None

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