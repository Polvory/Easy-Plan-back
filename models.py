from sqlalchemy import Column, Integer, String, DateTime, Boolean,  Text, Enum as SQLAlchemyEnum
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from db import Base
from enum import Enum
from schemas import TransactionsCategoriesEnum
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

class CategoriTypeEnum(str, Enum):
    admin = 'admin'
    user = 'user'
    
class LanguageTypeEnum(str, Enum):
    ru = 'ru'  # Русский
    kk = 'kk'  # Казахский
    cs = 'cs'  # Чешский
    en = 'en'  # Английский
    

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    apple_id = Column(String(50), unique=True, nullable=True)
    tg_id = Column(String(255), unique=True, nullable=True)
    tg_name = Column(String(255), unique=True, nullable=True)
    premium = Column(Boolean, default=False)
    premium_start = Column(DateTime(timezone=True), nullable=True)
    premium_expiration = Column(DateTime(timezone=True), nullable=True)
    email = Column(String(100), unique=True, nullable=True)
    role = Column(SQLAlchemyEnum(CategoriTypeEnum), default=CategoriTypeEnum.user)
    language = Column(SQLAlchemyEnum(LanguageTypeEnum), default=LanguageTypeEnum.en)
    
    # Определяем отношение к транзакциям
    transactions = relationship("Transactions", back_populates="user", cascade="all, delete-orphan")
    # Отношение к категориям
    user_categories = relationship(  # Изменено с "categories" для соответствия
        "Categories",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    # Отношение к счетам
    user_accounts = relationship( 
        "Accounts",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

class Transactions(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    sum = Column(Integer)
    currency = Column(SQLAlchemyEnum(CurrencyEnum), nullable=False)
    type = Column(SQLAlchemyEnum(TransactionsTypeEnum), default=TransactionsTypeEnum.income)

   # Связь с категорией
    category_id = Column(Integer, ForeignKey('categories.id', ondelete="CASCADE"), nullable=True)
    category = relationship(
        "Categories",
        back_populates="transactions"  # Должно соответствовать Categories.transactions
    )

    # Определяем отношение к пользователю
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Внешний ключ
    user = relationship("User", back_populates="transactions")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

class Categories(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    icon = Column(String(255), nullable=True)
    color = Column(String(255), nullable=False)
    svg = Column(Text, nullable=True)
    type = Column(String(255), nullable=False)
    moded = Column(String(255), nullable=False)
    
    # Отношение к транзакциям
    transactions = relationship(
        "Transactions",
        back_populates="category",  # Должно соответствовать Transactions.category
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="dynamic"
    )
    
    # Отношение к пользователю
    user_id = Column(Integer, ForeignKey('users.id', ondelete="SET NULL"), nullable=True)
    user = relationship(
        "User",
        back_populates="user_categories",  # Изменено с "categories" для ясности
        lazy="joined"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class Accounts(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    currency = Column(String(255), nullable=False)
    balance = Column(Integer, nullable=False, default=0)
    archive = Column(Boolean, default=False)  # Поле для архивации счета
     # Отношение к пользователю
    user_id = Column(Integer, ForeignKey('users.id', ondelete="SET NULL"), nullable=True)
    user = relationship(
        "User",
        back_populates="user_categories",  # Изменено с "categories" для ясности
        lazy="joined"
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
#  
# Счета
# Валюта
# Имя счета
# user_id
# summ



# транзакции
# Повтор операции
# Дата переодичности опреации
