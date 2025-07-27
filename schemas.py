# schemas.py
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from typing import List, Optional
from enums import CategoriTypeEnum, CurrencyEnum, LanguageTypeEnum, OperationReapitType, RepeatInterval, CurrencyEnum, TransactionsTypeEnum, AccountsUnderEnum
from decimal import Decimal




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
    balance: Decimal  
    archive: bool = False

class AccountCreate(AccountBase):
    name: str = Field(example="Сбер")
    currency: CurrencyEnum = Field(example="USD")
    balance: Decimal   = Field(example=300000)
    archive: bool = False

class AccountUpdate(AccountBase):
    name: Optional[str]= Field(None, example="Тинек")
    currency: Optional[CurrencyEnum] = Field(None, example="USD")
    balance: Optional[Decimal]   = Field(None, example=3000000)
    archive: Optional[bool] = Field(None, example=False)

class AccountResponse(AccountBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True   

class CreateLimit(BaseModel):
    balance:Decimal= Field(example=1300)
    category_id:int= Field(example=1)
    current_spent:Decimal= Field(example=0)
    date_update:str = Field(example="2025-06-01")
    
    
class LimitOut(BaseModel):
    id: int
    balance: Decimal
    current_spent:Decimal
    date_update: str
    user_id: int
    category_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # заменяет orm_mode в Pydantic v2
        
class LimitUpdate(BaseModel):
    balance:Decimal= Field(example=2300)
    date_update: str = Field(example="2025-06-01")



    
class CreateTarget(BaseModel):
    name: str = Field(example='На машину')
    balance_target: Decimal = Field(example=100000)
    account_id:int = Field(example=1)
    balance: Optional[Decimal] = 0
    date_end: date = Field(example="2025-07-01")
    completed: Optional[bool] = False
    svg: Optional[str] = None
    icon: Optional[str] = None
    
class TargetUpdate(BaseModel):
    name: Optional[str] = None
    balance_target: Optional[Decimal] = None
    balance: Optional[Decimal] = None
    date_end: Optional[date] = None
    completed: Optional[bool] = None
    svg: Optional[str] = None
    icon: Optional[str] = None
    
class TargetsOut(CreateTarget):
    id: int
    name: str
    balance_target: Decimal
    balance: Optional[Decimal] = 0
    date_end: date
    completed: Optional[bool] = False
    svg: Optional[str] = None
    icon: Optional[str] = None
    account_id:int
    account: Optional[AccountResponse] = None  # Добавляем аккаунт, если есть
     
class DebtsTransactionOut(BaseModel):
    id:int
    name:str
    who_gave:str
    date_take:str
    date_end: Optional[datetime] = None
    comments:str
    balance:Decimal
    completed:bool
    svg:str    

class ProjectBase(BaseModel):
    name: str = Field(default="Полет в Дубай")
    color: str = Field(default="#4232323")
    completed: Optional[bool] = False
    progress: Optional[int] = 0


class ProjectTransactionOut(ProjectBase):
    id: int
    name: str
    color: str
    completed: bool
    progress: int
    total:int

     
class TaskTransactioOut(BaseModel):
    id: int
    name: str
    # project:Optional[ProjectTransactionOut] = None  # Добавляем аккаунт, если есть  
        
class CreateTransaction(BaseModel):
    sum:Decimal = Field(example=1000)  # Было amount, должно быть sum
    moded: TransactionsTypeEnum = Field(example="income")  # ← теперь тип строго соответствует   
    repeat_operation: Optional[bool] = Field(default=False)  # Добавляем повторяющуюся операцию
    category_id: Optional[int] = Field(None, example=1)  # Добавляем ID категории
    account_id: Optional[int] = Field(example=1)  # Добавляем ID счета
    debt_id: Optional[int] = Field(None, example=None)  # Полностью необязательное поле
    target_id: Optional[int] = Field(None, example=None)  # Полностью необязательное поле
    task_id: Optional[int] = Field(None, example=None)  # Полностью необязательное поле
    date_operation: Optional[datetime] = Field(default=None, example="2023-12-31T23:59:59")
    class Config:
        orm_mode = True
    
class TransactionResponse(BaseModel):
    id: int
    sum: Decimal  
    balance: Decimal  
    currency: str
    moded: str
    category: Optional[CategoriesResponse]
    limit: Optional[CreateLimit]
    target: Optional[TargetsOut]
    debt: Optional[DebtsTransactionOut]
    task: Optional[TaskTransactioOut]
    
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
# Новый класс для сумм по дням
class DailySumResponse(BaseModel):
    date: date
    sum: Decimal  

class DailySumsResponse(BaseModel):
    value: Decimal  
    date: str  # Общая сумма за период

# Класс для общего ответа
class TransactionsWithStatsResponse(BaseModel):
    total: Decimal  
    daily_sums: List[DailySumResponse]  # Теперь массив вместо объекта
    transactions: List[TransactionResponse]
    graph_data:List[DailySumsResponse]
    
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
    timezone: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # transactions: List[TransactionResponse]  # Добавляем список транзакций
    # user_categories: List[CategoriesResponse]

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
    date_end:date
    comments:str
    balance:Decimal
    completed:bool
    svg:str
    account_id:int
    account: Optional[AccountResponse] = None  # Добавляем аккаунт, если есть
    transactions: List[TransactionResponse]  # Добавляем список транзакций
    transactions_sum: Optional[Decimal] = None  # Добавляем новое поле
     
class DebtsCreate(BaseModel):
    name:str = Field(example="На еду")
    account_id:int = Field(example=1)
    who_gave:str = Field(example="Петя Ивнов")
    date_take:str = Field(example="2025-05-01")
    date_end:str = Field(example="2025-06-01")
    comments:str = Field(example="Что-то")
    balance:Decimal= Field(example=30000)
    svg:str = Field(example="")

class DebtsUpdate(BaseModel):
    name: Optional[str] = None
    who_gave: Optional[str] = None
    date_take: Optional[str] = None
    date_end: Optional[str] = None
    comments: Optional[str] = None
    balance: Optional[float] = None
    svg: Optional[str] = None
    completed: Optional[bool] = None
    
class CreateOperationsRepeat(BaseModel):
    type: OperationReapitType = Field(..., example="transaction", description="Тип повторяющейся операции")
    interval: RepeatInterval = Field(..., example="month",  description="Интервал повторения day, week, month, year")
    repeat_date: datetime = Field(..., example="2023-01-01T00:00:00", description="Дата следующего повторения")
    repeat_count: int = Field(default=0, example=3, description="Количество оставшихся повторений")
    transaction_id: Optional[int] = Field(None, example=None)  # Полностью необязательное поле

  


class OperationsResponse(BaseModel):
        id:int
        repeat_date:datetime
        repeat_count:int
        interval:RepeatInterval
        type:OperationReapitType
        transaction: Optional[TransactionResponse]  # допускает None  # Добавляем список транзакций
        target_id: Optional[int] = None  # Полностью необязательное поле
        debt_id: Optional[int] = None  # Полностью необязательное поле
        
class OperationsWithLimitsResponse(BaseModel):
        total: int
        reapits:List[OperationsResponse]
        


class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    completed: Optional[bool] = None
    progress: Optional[int] = None

class ProjectOut(ProjectBase):
    id: int

    class Config:
        orm_mode = True


        
class TaskCreate(BaseModel):
    name: str  = Field(default="Билеты", example="Концерт")
    date_end: datetime = Field(example="2023-12-31T23:59:59")
    sum: Optional[Decimal] = Field(default=None, example=5000)
    comments: Optional[str] = Field(default=None, example="Купить 2 билета")
    completed: Optional[bool] = False
    moded: Optional[TransactionsTypeEnum] = Field(default=None, example="expense")
    project_id: int = Field(default=1, example=1)
    account_id: Optional[int] = Field(default=None, example=1)
    class Config:
        schema_extra = {
            "example": {
                "date_end": "2023-12-31T23:59:59",
                "project_id": 42,
                # Остальные поля не переданы - будут NULL
            }
        }
 

class TaskUpdate(BaseModel):
    
    name: Optional[str]  = Field(default="Билеты", example="Концерт")
    date_end: Optional[datetime] = Field(default=None, example="2023-12-31T23:59:59")
    sum: Optional[Decimal] = Field(default=None, example=5000)
    comments: Optional[str] = Field(default=None, example="Купить 2 билета")
    completed: Optional[bool] = False
    moded: Optional[TransactionsTypeEnum] = Field(default=None, example="expense")
    project_id: Optional[int] = Field(default=1, example=1)
    account_id: Optional[int] = Field(default=None, example=1)
    
 

class TaskOut(TaskCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    account: Optional[AccountResponse] = None  # Добавляем аккаунт, если есть
    transaction: Optional[TransactionResponse] = None  
    class Config:
        orm_mode = True

class TaskUpdateOut(BaseModel):
        task:TaskOut
        transaction_status:str

class ProjectTaskOut(BaseModel):
    id: int
    name: Optional[str] = None  # Теперь принимает и None, и строку
    sum: Decimal
    date_end: datetime
    comments: Optional[str] = None  # Теперь принимает и None, и строку
    completed:bool
    moded:str
    account_id: int
    
    model_config = ConfigDict(from_attributes=True)

class ProjectResponse(BaseModel):
    id: int
    name: str
    color: str
    completed: bool
    progress: int
    tasks:List[ProjectTaskOut] = None 
    total:int
    total_sum: Decimal  # Сумма всех задач
    class Config:
        orm_mode = True

class ProjectResponseWithTotal(BaseModel):
        projects:List[ProjectResponse] = []  # Список задач, если есть
        total:int

class RepeatOperationOut(BaseModel):
    id:int
    balance: Decimal
    moded: Optional[str] = None  # Тип операции, может быть None
    completed: Optional[bool] = False  # Статус выполнения операции
    name: Optional[str] = None  # Название операции, может быть None
    category: Optional[CategoriesResponse] = None  
    account: Optional[AccountResponse] = None  # Добавляем аккаунт, если есть
    debt: Optional[DebtsTransactionOut] = None 
    target: Optional[TargetsOut] = None 
    limit: Optional[CreateLimit] = None    
    task: Optional[TaskTransactioOut] = None  
    planned_date: date
    created_at: datetime
    updated_at: datetime
# Pydantic-схема для создания операции повторения
class CreateRepeatOperation(BaseModel):
    balance: Decimal = Field(..., description="Баланс операции")
    date_start:str = Field(..., example="2025-06-09")
    moded: TransactionsTypeEnum = Field(..., example="expense", description="Тип операции")
    # transaction_id: Optional[int] = Field(None, description="ID транзакции")
    name : Optional[str] = Field(None, description="Название операции")
    category_id:  Optional[int] = Field(None, description="ID категории")
    account_id:  Optional[int] = Field(..., example=1, description="ID счета")
    debt_id: Optional[int] = Field(None, description="ID долга")
    target_id: Optional[int] = Field(None, description="ID цели")
    limit_id: Optional[int] = Field(None, description="ID лимита")
    task_id: Optional[int] = Field(None, description="ID задачи")
    interval: RepeatInterval = Field(..., example="day",  description="Интервал повторения day, week, month, year")
    count: int = Field(default=5, description="Количество повторений операции")
    
class RepeatOperationListOut(BaseModel):
    total: int
    reapits: List[RepeatOperationOut]  # Список операций повторения