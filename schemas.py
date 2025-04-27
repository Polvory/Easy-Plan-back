# schemas.py
from enum import Enum
from pydantic import BaseModel
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