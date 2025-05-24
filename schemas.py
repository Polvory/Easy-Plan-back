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

class AccountsUnderEnum(str, Enum):
    goals = 'goals' # Цели
    limits = 'limits' # Правила
    debts = 'debts' # Долги

class RefreshTokenRequest(BaseModel):
    refresh_token: str

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

class CreateLimit(BaseModel):
    balance:int= Field(example=1300)
    category_id:int= Field(example=1)
    current_spent:int= Field(example=0)
    date_update:str = Field(example="2025-06-01")
    
    
class LimitOut(BaseModel):
    id: int
    balance: int
    current_spent:int
    date_update: str
    user_id: int
    category_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # заменяет orm_mode в Pydantic v2
        
class LimitUpdate(BaseModel):
    balance:int= Field(example=2300)
    date_update: str = Field(example="2025-06-01")



    
class CreateTarget(BaseModel):
    name: str
    balance_target: int
    balance: Optional[int] = 0
    date_end: str
    completed: Optional[bool] = False
    svg: Optional[str] = None

class TargetUpdate(BaseModel):
    name: Optional[str] = None
    balance_target: Optional[int] = None
    balance: Optional[int] = None
    date_end: Optional[str] = None
    completed: Optional[bool] = None
    svg: Optional[str] = None

class TargetsOut(CreateTarget):
    id: int
    name: str
    balance_target: int
    balance: Optional[int] = 0
    date_end: str
    completed: Optional[bool] = False
    svg: Optional[str] = None
     
        
        
        
class CreateTransaction(BaseModel):
    sum:int = Field(example=1000)  # Было amount, должно быть sum
    moded: TransactionsTypeEnum = Field(example="income")  # ← теперь тип строго соответствует   
    repeat_operation: Optional[bool] = Field(default=False)  # Добавляем повторяющуюся операцию
    category_id: Optional[int] = Field(example=1)  # Добавляем ID категории
    account_id: Optional[int] = Field(example=1)  # Добавляем ID счета
    debt_id: Optional[int] = Field(None, example=None)  # Полностью необязательное поле
    target_id: Optional[int] = Field(None, example=None)  # Полностью необязательное поле

    class Config:
       schema_extra = {
            "example": {
                "sum": 1000,
                "moded": "income",
                "repeat_operation": False,
                "category_id": 1,
                "account_id": 1,
                "debt_id": None
            }
        }
    
class TransactionResponse(BaseModel):
    id: int
    sum: int
    balance: int
    currency: str
    moded: str
    category: Optional[CategoriesResponse]
    limit: Optional[CreateLimit]
    target: Optional[TargetsOut]
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
    
class DebtsResponse(BaseModel):
    id:int
    name:str
    who_gave:str
    date_take:str
    date_end:str
    comments:str
    balance:int
    completed:bool
    svg:str
    transactions: List[TransactionResponse]  # Добавляем список транзакций
    transactions_sum: Optional[float] = None  # Добавляем новое поле
     
class DebtsCreate(BaseModel):
    name:str = Field(example="На еду")
    who_gave:str = Field(example="Петя Ивнов")
    date_take:str = Field(example="2025-05-01")
    date_end:str = Field(example="2025-06-01")
    comments:str = Field(example="Что-то")
    balance:int= Field(example=30000)
    svg:str = Field(example="")

class DebtsUpdate(BaseModel):
    name: Optional[str] = None
    who_gave: Optional[str] = None
    date_take: Optional[str] = None
    date_end: Optional[str] = None
    comments: Optional[str] = None
    balance: Optional[int] = None
    svg: Optional[str] = None
    completed: Optional[bool] = None
    
