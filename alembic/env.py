import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Добавляем путь до проекта, чтобы работал импорт моделей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импортируем Base и модели
from db import Base
from models import (
    # Feature_limits,
    User,
    # Transactions,
    # Categories,
    # Accounts,
    # Limits,
    # Debts,
    # Targets,
    # RepeatOperations,
    # OperationsRepeat,
    # Project,
    # Tasks,
)

# Конфигурация Alembic
config = context.config

# Настройка логирования (по alembic.ini)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Устанавливаем метаданные моделей
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Миграции в 'offline' режиме — без подключения к БД.
    Просто генерирует SQL.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,  # 👈 важно для отслеживания изменения типов колонок
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Миграции в 'online' режиме — с подключением к базе данных.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # 👈 тоже важно
        )

        with context.begin_transaction():
            context.run_migrations()


# Запускаем нужный режим
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
