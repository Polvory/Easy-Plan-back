from enum import Enum

class CategoriTypeEnum(str, Enum):
    admin = 'admin'
    user = 'user'


class limit_subscription():
    account_management = 1
    planning = 2
    liabilities = 2
    task_tracker = 3
    limits = 2
    debts = 1
    open_ai_balanse = 3
    open_tsak = 3

# Определяем перечисление допустимых валют
class CurrencyEnum(str, Enum):
    RUB = "RUB"  # Российский рубль
    KZT = "KZT"  # Казахстанский тенге
    CNY = "CNY"  # Китайский юань
    CZK = "CZK"  # Чешская крона
    USD = "USD"  # Доллар США

class LanguageTypeEnum(str, Enum):
    ru = 'ru'
    kk = 'kk'
    cs = 'cs'
    en = 'en'
    

class OperationReapitType(str, Enum):
   target = "target" 
   debt = "debt" 
   limit = "limit" 
   transaction = "transaction"

class RepeatInterval(str, Enum):
    DAILY = "day"
    WEEKLY = "week"
    MONTHLY = "month"
    YEARLY = "year"
    
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