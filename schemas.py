# schemas.py
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional



# Определяем перечисление допустимых валют
class CurrencyEnum(str, Enum):
    RUB = "RUB"  # Российский рубль
    KZT = "KZT"  # Казахстанский тенге
    CNY = "CNY"  # Китайский юань
    CZK = "CZK"  # Чешская крона
    USD = "USD"  # Доллар США
    
class TransactionsTypeEnum(str, Enum):
    income = 'income'
    expense = 'expense'





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
    
    
class AccountBase(BaseModel):
    name: str
    currency: str
    balance: int
    archive: bool = False

class AccountCreate(AccountBase):
    name: str = Field(example="Сбер")
    currency: CurrencyEnum = Field(example="USD")
    balance: int = Field(example=300000)
    archive: bool = False

class AccountUpdate(AccountBase):
    name: Optional[str]= Field(example="Тинек")
    currency: CurrencyEnum = Field(example="USD")
    balance: int = Field(example=3000000)
    # archive: bool = False

class AccountResponse(AccountBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True   


class CreateTransaction(BaseModel):
    sum:int = Field(example=1000)  # Было amount, должно быть sum
    moded: TransactionsTypeEnum = Field(example="income")  # ← теперь тип строго соответствует   
    repeat_operation: Optional[bool] = Field(default=False)  # Добавляем повторяющуюся операцию
    category_id: Optional[int] = Field(example=1)  # Добавляем ID категории
    account_id: Optional[int] = Field(example=1)  # Добавляем ID счета
    class Config:
        orm_mode = True
    
class TransactionResponse(BaseModel):
    id: int
    sum: int
    balance: int
    currency: str
    moded: str
    category: Optional[CategoriesResponse]
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

class UserFinance(BaseModel):
    id: int    
    transactions: List[TransactionResponse]  # Добавляем список транзакций

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_data:object