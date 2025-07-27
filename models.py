from enum import Enum
from sqlalchemy import (
    Column, Integer, Numeric, String, DateTime, Boolean, Text,
    ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum
from db import Base
from enums import CategoriTypeEnum, CurrencyEnum, LanguageTypeEnum, OperationReapitType, RepeatInterval, CurrencyEnum, TransactionsTypeEnum, AccountsUnderEnum



class Feature_limits(Base):
    __tablename__ = "feature_limits"
    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    user = relationship("User", back_populates="feature_limits", uselist=False)
    
    subscription_type = Column(String, nullable=False, index=True)
    account_management = Column(Integer, default=1)
    goals = Column(Integer, default=2) # цели
    tasks = Column(Integer, default=3)
    limits = Column(Integer, default=2)
    debts = Column(Integer, default=1)
    open_ai_balance = Column(Integer, default=3)
    open_ai_tasks = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    apple_id = Column(String(50), unique=True, nullable=True)
    tg_id = Column(String(255), unique=True, nullable=True)
    tg_name = Column(String(255), unique=True, nullable=True)
    

    # Платежка
    premium = Column(Boolean, default=False)
    premium_type = Column(String(255), nullable=True)
    payment_profile_id = Column(String(255), nullable=True)
    payment_customer_user_id = Column(String(255), nullable=True)
    payment_is_active = Column(Boolean, default=False)
    payment_starts_at = Column(DateTime(timezone=True), server_default=func.now())
    payment_expires_at = Column(DateTime(timezone=True), server_default=func.now())
    
    feature_limits = relationship("Feature_limits", back_populates="user", uselist=False, cascade="all, delete-orphan")
    timezone = Column(String(255), nullable=True)
    
    limit_reqwest_tasks = Column(Integer, default=100)  # Лимит запросов на задачи
    limit_reqwest_balance_forecast = Column(Integer, default=2)  # Лимит запросов на прогноз баланса в день
    
    
    
    email = Column(String(100), unique=True, nullable=True)
    role = Column(SQLAlchemyEnum(CategoriTypeEnum), default=CategoriTypeEnum.user)
    language = Column(SQLAlchemyEnum(LanguageTypeEnum), default=LanguageTypeEnum.en)

    transactions = relationship("Transactions", back_populates="user", cascade="all, delete-orphan")
    debts = relationship("Debts", back_populates="user", cascade="all, delete-orphan")
    user_categories = relationship("Categories", back_populates="user", cascade="all, delete-orphan")
    user_accounts = relationship("Accounts", back_populates="user", cascade="all, delete-orphan")
    user_limits = relationship("Limits", back_populates="user", cascade="all, delete-orphan")
    user_targets = relationship("Targets", back_populates="user", cascade="all, delete-orphan")
    user_operations_repeat = relationship("OperationsRepeat", back_populates="user", cascade="all, delete-orphan")
    user_project = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    # Связь без каскадного удаления операций:
    repeat_operations = relationship("RepeatOperations", back_populates="user", passive_deletes=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Transactions(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    sum = Column(Numeric(10, 2))
    currency = Column(SQLAlchemyEnum(CurrencyEnum), nullable=False)
    moded = Column(String(255), nullable=False)
    repeat_operation = Column(Boolean, default=False)
    balance = Column(Numeric(10, 2))
    # completed = Column(Boolean, default=False)  # Статус выполнения операции

    category_id = Column(Integer, ForeignKey('categories.id', ondelete="SET NULL"), nullable=True)
    category = relationship("Categories", back_populates="transactions")

    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    account = relationship("Accounts", back_populates="transactions")

    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=False)
    user = relationship("User", back_populates="transactions")

    debt_id = Column(Integer, ForeignKey('debts.id', ondelete='SET NULL'), nullable=True)
    debt = relationship("Debts", back_populates="transactions")
    
    target_id = Column(Integer, ForeignKey('targets.id', ondelete='SET NULL'), nullable=True)
    target = relationship("Targets", back_populates="transactions")
    
    limit_id = Column(Integer, ForeignKey('limits.id', ondelete='SET NULL'), nullable=True)
    limit = relationship("Limits", back_populates="transactions")
    
     # Внешний ключ для связи с Tasks
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True)
    operations_repeat = relationship("OperationsRepeat", back_populates="transaction", passive_deletes=True)
    # Связь один-к-одному (Transaction -> Task)
    task = relationship(
        "Tasks", 
        back_populates="transaction",
        uselist=False
    )
    
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

    repeat_operations = relationship("RepeatOperations", back_populates="category", passive_deletes=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Accounts(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    currency = Column(String, nullable=False)
    balance = Column(Numeric(10, 2), nullable=False, default=0)
    archive = Column(Boolean, default=False)

    repeat_operations = relationship("RepeatOperations", back_populates="account", passive_deletes=True)

    
    debts = relationship("Debts", back_populates="account", cascade="all, delete-orphan") 
    targets = relationship("Targets", back_populates="account", cascade="all, delete-orphan") 
    
    
    
    transactions = relationship("Transactions", back_populates="account", cascade="all, delete-orphan")
    tasks = relationship("Tasks", back_populates="account", cascade="all, delete-orphan")

    user_id = Column(Integer, ForeignKey('users.id', ondelete="SET NULL"), nullable=True)
    user = relationship("User", back_populates="user_accounts", lazy="joined")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


    
class Limits(Base):
    __tablename__ = "limits"
    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Numeric(10, 2), nullable=False)
    date_update = Column(String(255), nullable=False)
    current_spent = Column(Integer, default=0)  # сколько потрачено
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="user_limits")
    
    category_id = Column(Integer, ForeignKey('categories.id', ondelete="CASCADE"), nullable=True)
    category = relationship("Categories", back_populates="limit")
    
    transactions = relationship(
        "Transactions",
        back_populates="limit",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="dynamic"
    )
    
    repeat_operations = relationship("RepeatOperations", back_populates="limit", passive_deletes=True)

    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    
    

#  если надо повторять то мы закидываем в таблицу операций для репита если цель есть в репите срок продливаем или создаем новую цель    
    
    
    

   

class Debts(Base):
    __tablename__ = "debts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    who_gave = Column(Text, nullable=False)
    date_take = Column(String(255), nullable=False)
    date_end = Column(DateTime(timezone=True), server_default=func.now())
    comments = Column(Text, nullable=False)
    balance = Column(Numeric(10, 2))
    svg = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)


    transactions = relationship(
        "Transactions",
        back_populates="debt",
        cascade="all, delete-orphan"
    )
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    account = relationship("Accounts", back_populates="debts")
        # Необязательная связь один-к-одному с OperationsRepeat
    operations_repeats = relationship(
        "OperationsRepeat",
        back_populates="debt",
        cascade="all, delete-orphan"
    )
    repeat_operations = relationship("RepeatOperations", back_populates="debt", passive_deletes=True)
    
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="debts")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    
class Targets(Base):
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    balance_target = Column(Numeric(10, 2), nullable=False)
    balance = Column(Numeric(10, 2), nullable=False, default=0)
    date_end = Column(DateTime(timezone=True), nullable=False)
    completed = Column(Boolean, default=False)
    svg = Column(Text, nullable=True)
    icon = Column(String(255), nullable=True)
    
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    account = relationship("Accounts", back_populates="targets")
    
    transactions = relationship(
        "Transactions",
        back_populates="target",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="dynamic"
    )     
         # Необязательная связь один-к-одному с OperationsRepeat
    operations_repeats = relationship(
        "OperationsRepeat",
        back_populates="target",
        cascade="all, delete-orphan"
    )
    
    repeat_operations = relationship("RepeatOperations", back_populates="target", passive_deletes=True)
    
    
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="user_targets") 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    

class RepeatOperations(Base):
    __tablename__ = "repeat_operations"
    id = Column(Integer, primary_key=True, index=True)  
    balance = Column(Numeric(10, 2))
    moded = Column(String(255), nullable=False)
    planned_date = Column(DateTime(timezone=True), nullable=False)
    name = Column(Text, nullable=False)  # Название операции
    completed = Column(Boolean, default=False)  # Статус выполнения операции
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=False)
    user = relationship("User", back_populates="repeat_operations", passive_deletes=True)
    
    # +++
    category_id = Column(Integer, ForeignKey('categories.id', ondelete="SET NULL"), nullable=True)
    category = relationship("Categories", back_populates="repeat_operations", passive_deletes=True)
    
    # +++
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=False)
    account = relationship("Accounts", back_populates="repeat_operations", passive_deletes=True)
   
    # +++
    debt_id = Column(Integer, ForeignKey('debts.id', ondelete='SET NULL'), nullable=True)
    debt = relationship("Debts", back_populates="repeat_operations", passive_deletes=True)
   
    # +++
    target_id = Column(Integer, ForeignKey('targets.id', ondelete='SET NULL'), nullable=True)
    target = relationship("Targets", back_populates="repeat_operations", passive_deletes=True)
    
    # +++
    limit_id = Column(Integer, ForeignKey('limits.id', ondelete='SET NULL'), nullable=True)
    limit = relationship("Limits", back_populates="repeat_operations", passive_deletes=True)
    
    # Внешний ключ для связи с Tasks
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True)
    task = relationship("Tasks", back_populates="repeat_operations", passive_deletes=True)  # без uselist=False
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
       

class OperationsRepeat(Base):
    __tablename__ = "operations_repeat"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(255), nullable=False)  # Тип операции, например "target" или "debts" "limits" "transaction"
    interval = Column(String(255), nullable=False)
    
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="user_operations_repeat") 

    # Связь с Transactions (необязательная)
    transaction_id = Column(
        Integer, 
        ForeignKey('transactions.id', ondelete="CASCADE"), 
        nullable=True  # Изменили на True, чтобы связь была необязательной
    )
    transaction = relationship("Transactions", back_populates="operations_repeat")
    
    # Связь с Debts (необязательная)
    debt_id = Column(
        Integer, 
        ForeignKey('debts.id', ondelete="CASCADE"), 
        nullable=True  # Необязательная связь
    )
    debt = relationship("Debts", back_populates="operations_repeats")  # back_populates должен совпадать с именем в Debts
    
    # Связь с Debts (необязательная)
    target_id = Column(
        Integer, 
        ForeignKey('targets.id', ondelete="CASCADE"), 
        nullable=True  # Необязательная связь
    )
    target = relationship("Targets", back_populates="operations_repeats")
   
    
    repeat_date = Column(DateTime(timezone=True), server_default=func.now())
    repeat_count = Column(Integer, default=0)  # Количество повторений операции
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())



class Project(Base):
    __tablename__ = "project"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    color = Column(String(255), nullable=False)
    completed = Column(Boolean, default=False)
    progress = Column(Integer, default=0)  # Прогресс выполнения проекта в процентах
    
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="user_project") 
    
    tasks = relationship("Tasks", back_populates="project", cascade="all, delete-orphan")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())




class Tasks(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    date_end = Column(DateTime(timezone=True), nullable=False)
    sum = Column(Numeric(10, 2), nullable=True, default=0)  # Сумма или стоимость задачи
    comments = Column(Text, nullable=True)  # Комментарии к задаче
    completed = Column(Boolean, default=False)  # Статус выполнения задачи
    moded = Column(String(255), nullable=True)
    project_id = Column(Integer, ForeignKey('project.id', ondelete="CASCADE"), nullable=False)
    project = relationship("Project", back_populates="tasks")
    
    
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)
    account = relationship("Accounts", back_populates="tasks")
    
    
    
   # Связь один-к-одному с Transactions (Task -> Transaction)
    transaction = relationship(
        "Transactions", 
        back_populates="task",
        uselist=False,
        cascade="save-update, merge"  # Добавлено для синхронизации  # Каскадное удаление здесь
    )
    
    # Добавляем обратную связь на RepeatOperations — 1 задача может иметь много repeat операций
    repeat_operations = relationship("RepeatOperations", back_populates="task", passive_deletes=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
