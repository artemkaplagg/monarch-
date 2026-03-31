# main.py – MONARCH BOT

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

logging.basicConfig(
level=logging.INFO,
format=”%(asctime)s | %(levelname)s | %(name)s | %(message)s”,
datefmt=”%H:%M:%S”,
)
log = logging.getLogger(“MONARCH”)

async def main():
log.info(“MONARCH SYSTEM – START”)

```
init_db()
log.info("DB ready.")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2),
)

dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

scheduler = setup_scheduler(bot, USER_ID, CHANNEL_ID)
scheduler.start()
log.info("Scheduler started. Jobs: %d", len(scheduler.get_jobs()))
log.info("Bot started. USER_ID=%s CHANNEL_ID=%s", USER_ID, CHANNEL_ID)

try:
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
finally:
    scheduler.shutdown(wait=False)
    await bot.session.close()
    log.info("MONARCH SYSTEM -- STOPPED")
```

if **name** == “**main**”:
asyncio.run(main())
