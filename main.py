# main.py — MONARCH BOT

# Точка входа. Чисто. Без мусора.

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, USER_ID, CHANNEL_ID
from models import init_db
from handlers import router
from tasks import setup_scheduler

# ─────────────────────────────────────────────

# ЛОГИРОВАНИЕ

# ─────────────────────────────────────────────

logging.basicConfig(
level=logging.INFO,
format=”%(asctime)s | %(levelname)s | %(name)s | %(message)s”,
datefmt=”%H:%M:%S”,
)
log = logging.getLogger(“MONARCH”)

# ─────────────────────────────────────────────

# ТОЧКА ВХОДА

# ─────────────────────────────────────────────

async def main():
log.info(“MONARCH SYSTEM — ЗАПУСК”)

```
# БД — создаём таблицы если нет
log.info("Инициализация базы данных...")
init_db()
log.info("БД готова.")

# Бот
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2),
)

# Диспетчер
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

# Планировщик
log.info("Запуск планировщика...")
scheduler = setup_scheduler(bot, USER_ID, CHANNEL_ID)
scheduler.start()
log.info(f"Планировщик активен. Задач: {len(scheduler.get_jobs())}")

# Старт
log.info(f"Бот запущен. USER_ID={USER_ID} | CHANNEL_ID={CHANNEL_ID}")
try:
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
finally:
    scheduler.shutdown(wait=False)
    await bot.session.close()
    log.info("MONARCH SYSTEM — ОСТАНОВЛЕН")
```

if **name** == “**main**”:
asyncio.run(main())
