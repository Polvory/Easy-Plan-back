from datetime import datetime
import logging
from typing import Optional
from sqlalchemy.orm import Session
from auth.auth import TokenPayload, guard_role
from db import SessionLocal
from fastapi import APIRouter, Body, HTTPException, status, Depends, Query
import httpx
import json
from pydantic import BaseModel
from routers.balance_forecast import get_operations
import asyncio

from routers.limite_pyment import subtract_open_ai_balance, subtract_open_ai_tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai",
    tags=["ai"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Pydantic модель для тела запроса
class PromptRequest(BaseModel):
    prompt: str
    
    
    
@router.post("/finance", summary="Финансовая консультация прогноз (admin/user)")
async def finance_ask(  
            db: Session = Depends(get_db),
            
            current_user: TokenPayload = Depends(guard_role(["admin", "user" ], limit_key="open_ai_balance")),
            account_id: int = Query(None, description="id счета", example=1),
            date_from: Optional[datetime] = Query(None, description="Начальная дата для фильтрации (planned_date >= date_from)", example="2025-05-01"),
            date_to: Optional[datetime] = Query(None, description="Конечная дата для фильтрации (planned_date <= date_to)", example="2025-12-30"),
                      ):
   
        user_current_data = TokenPayload(
                        user_id=current_user.user_id,
                        roles=["user"],  # или operation.user.roles если есть такое поле
                        role="user",     # если модель требует отдельное поле role
                        language="ru"    # или другое значение по умолчанию
                )
        operations = get_operations(db, user_current_data, account_id, date_from, date_to)

# Ты профессиональный финансовый консультант. На основе предоставленных будущих финансовых операций (доходы и расходы с датами и остатками на счёте), проанализируй моё финансовое состояние и сделай прогноз.
#  Формат данных:
#             - name: Название операции
#             - date: Дата операции
#             - balance: Сумма
#             - moded: Тип ("income" — доход, "expense" — расход)
#             - balance_forecast: прогнозируемый остаток после операции
#             Твоя задача:
#             1. Сформулировать **финансовый прогноз** на основе динамики доходов и расходов.
#             2. Дать оценку **достижимости финансовых целей**, если они видны из данных.
#             3. Указать **возможные финансовые риски** (например, недостаток дохода, рост обязательств, низкая диверсификация).
#             4. При необходимости — предложи **рекомендации по улучшению финансовой устойчивости**.

        promt = f"""
            

            
            
            Составь детализированный финансовый прогноз и рекомендации на русском языке в формате приложения, используя данные из JSON: поступления (доходы), траты (расходы), финансовая цель, текущие накопления, ежемесячная сумма для откладывания, задачи с датами и суммами, форматируя с заголовком ‘Финансовый прогноз’ и иконкой, секцией ‘Финансовый прогноз’ с таблицей доходов/расходов по месяцам, разницей (положительные значения зеленым, например, ‘+5 000 ₽’) и аналитикой (мин/макс/средний остаток), секцией ‘Цель’ с названием, суммой, накоплениями, сроком достижения (месяцы/годы) на основе текущей системной даты, текстовым прогресс-баром (например, ‘[████░░░░░░░░ 20%]’), секцией ‘Задачи’ с перечнем задач, датами выполнения и суммами, оценивая возможность выполнения обязательств (сумма расходов и задач минус доходы) и предлагая перенос сроков задач на более благоприятный период, если финансы недостаточны, и секцией ‘Рекомендации’ с оценкой ситуации, пятью вариантами (увеличение откладываний на 5 000 ₽, инвестиции 5 000 ₽/мес с доходностью 5%, сокращение расходов на 10 000 ₽/мес, комбинированный подход +10 000 ₽/мес, дополнительный доход 15 000 ₽/мес) с новыми сроками и прогресс-барами, и мотивационным советом, структурируя как на мобильном экране с символами ₽, адаптируя под динамические данные и строго используя текущую системную дату без предположений.
            Ответ пришли толко текстом не JSON !
           

            Вот данные: {operations}
            """
            
        
        print(promt)
      
        url = "http://147.45.171.136/castom_task"
        headers = {"Content-Type": "application/json"}
        json_body = {"prompt": promt}



        retries = 2
        timeout = httpx.Timeout(15.0, connect=5.0)

        for attempt in range(1, retries + 2):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, headers=headers, json=json_body)
                    response.raise_for_status()
                    data = response.json()
                    subtract_open_ai_balance(db, current_user.user_id)
                    json_str = data.get("response", "")
                    if not json_str:
                        logger.error("Пустой ответ в поле 'response'")
                        raise HTTPException(status_code=500, detail="Пустой ответ от внешнего сервера")
                    logger.info(f"Получен ответ: {json_str}")
                    text_response = json_str.replace('\\n', '\n').replace('\\"', '"').strip('"')
                    return {"response": text_response}
                    # return {"response": json_str}
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning(f"[Попытка {attempt}] Ошибка запроса: {e}")
                if attempt <= retries:
                    await asyncio.sleep(1)  # задержка перед следующей попыткой
                else:
                    logger.error(f"Все попытки исчерпаны: {e}")
                    raise HTTPException(status_code=502, detail=f"Ошибка связи с внешним сервером: {e}")
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")
                raise HTTPException(status_code=500, detail="Ошибка обработки данных от внешнего сервера")
       


@router.post("/task", summary="Запрос к таскам (admin/user)")
async def ask_task(
    current_user: TokenPayload = Depends(guard_role(["admin", "user" ], limit_key="open_ai_tasks")),
    prompt: PromptRequest = Body(..., description="Текст запроса для AI"),
    db: Session = Depends(get_db)
):
    url = "http://147.45.171.136/task"
    headers = {"Content-Type": "application/json"}
    json_body = {"prompt": prompt.prompt}

    retries = 2
    timeout = httpx.Timeout(15.0, connect=5.0)

    for attempt in range(1, retries + 2):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=json_body)
                response.raise_for_status()
                subtract_open_ai_tasks(db, current_user.user_id)
                data = response.json()
                json_str = data.get("response", "")
                if not json_str:
                    logger.error("Пустой ответ в поле 'response'")
                    raise HTTPException(status_code=500, detail="Пустой ответ от внешнего сервера")

                parsed = json.loads(json_str)
                logger.info(f"Получен ответ: {parsed}")
                return parsed

        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(f"[Попытка {attempt}] Ошибка запроса: {e}")
            if attempt <= retries:
                await asyncio.sleep(1)
            else:
                raise HTTPException(status_code=502, detail=f"Ошибка связи с внешним сервером: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            raise HTTPException(status_code=500, detail="Ошибка обработки данных от внешнего сервера")