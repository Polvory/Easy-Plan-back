from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://postgres:1234@localhost:5432/easy_plan_db"

try:
    # Создание движка подключения
    engine = create_engine(DATABASE_URL)

    # Пробуем подключиться к базе
    with engine.connect() as connection:
        print("✅ Успешное подключение к PostgreSQL через SQLAlchemy!")

    # Создание сессии
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Базовый класс для моделей
    Base = declarative_base()

except Exception as e:
    print("❌ Ошибка подключения к базе данных:", e)
