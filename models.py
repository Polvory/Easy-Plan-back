from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text,
    ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum
from db import Base
from schemas import CurrencyEnum, TransactionsTypeEnum


class CategoriTypeEnum(str, Enum):
    admin = 'admin'
    user = 'user'


class LanguageTypeEnum(str, Enum):
    ru = 'ru'
    kk = 'kk'
    cs = 'cs'
    en = 'en'


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

    transactions = relationship("Transactions", back_populates="user", cascade="all, delete-orphan")
    debts = relationship("Debts", back_populates="user", cascade="all, delete-orphan")
    user_categories = relationship("Categories", back_populates="user", cascade="all, delete-orphan")
    user_accounts = relationship("Accounts", back_populates="user", cascade="all, delete-orphan")
    user_limits = relationship("Limits", back_populates="user", cascade="all, delete-orphan")
    user_targets = relationship("Targets", back_populates="user", cascade="all, delete-orphan")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Transactions(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    sum = Column(Integer)
    currency = Column(SQLAlchemyEnum(CurrencyEnum), nullable=False)
    moded = Column(String(255), nullable=False)
    repeat_operation = Column(Boolean, default=False)
    balance = Column(Integer)

    category_id = Column(Integer, ForeignKey('categories.id', ondelete="CASCADE"), nullable=True)
    category = relationship("Categories", back_populates="transactions")

    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    account = relationship("Accounts", back_populates="transactions")

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="transactions")

    debt_id = Column(Integer, ForeignKey('debts.id'), nullable=True)
    debt = relationship("Debts", back_populates="transactions")
    
    
    
    target_id = Column(Integer, ForeignKey('targets.id'), nullable=True)
    target = relationship("Targets", back_populates="transactions")
    
    limit_id = Column(Integer, ForeignKey('limits.id', ondelete='SET NULL'), nullable=True)
    limit = relationship("Limits", back_populates="transactions")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())



class Categories(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    icon = Column(String(255), nullable=True)
    color = Column(String(255), nullable=False)
    svg = Column(Text, nullable=True)
    type = Column(String(255), nullable=False)
    moded = Column(String(255), nullable=False)

    transactions = relationship(
        "Transactions",
        back_populates="category",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="dynamic"
    )

    user_id = Column(Integer, ForeignKey('users.id', ondelete="SET NULL"), nullable=True)
    user = relationship("User", back_populates="user_categories", lazy="joined")

    limit = relationship("Limits", back_populates="category", uselist=False)


    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Accounts(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    currency = Column(String(255), nullable=False)
    balance = Column(Integer, nullable=False, default=0)
    archive = Column(Boolean, default=False)

    transactions = relationship("Transactions", back_populates="account", cascade="all, delete-orphan")

    user_id = Column(Integer, ForeignKey('users.id', ondelete="SET NULL"), nullable=True)
    user = relationship("User", back_populates="user_accounts", lazy="joined")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    
    
class Limits(Base):
    __tablename__ = "limits"
    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Integer, nullable=False)
    date_update = Column(String(255), nullable=False)
    current_spent = Column(Integer, default=0)  # сколько потрачено
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="user_limits")
    
    category_id = Column(Integer, ForeignKey('categories.id', ondelete="SET NULL"), nullable=True)
    category = relationship("Categories", back_populates="limit")
    
    transactions = relationship(
        "Transactions",
        back_populates="limit",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="dynamic"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    
    
class Debts(Base):
    __tablename__ = "debts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    who_gave = Column(Text, nullable=False)
    date_take = Column(String(255), nullable=False)
    date_end = Column(String(255), nullable=False)
    comments = Column(Text, nullable=False)
    balance = Column(Integer)
    svg = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)

    transactions = relationship(
        "Transactions",
        back_populates="debt",
        cascade="all, delete-orphan"
    )

    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="debts")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
#  если надо повторять то мы закидываем в таблицу операций для репита если цель есть в репите срок продливаем или создаем новую цель    
    
    
    
class Targets(Base):
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    balance_target = Column(Integer, nullable=False)
    balance = Column(Integer, nullable=False, default=0)
    date_end = Column(String(255), nullable=False)
    completed = Column(Boolean, default=False)
    svg = Column(Text, nullable=True)
    
    transactions = relationship(
        "Transactions",
        back_populates="target",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="dynamic"
    )     
    
    
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="user_targets") 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
   
    


