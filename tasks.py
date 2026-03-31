# tasks.py — MONARCH BOT

# APScheduler: утро / вечер / автоштраф / еженедельный отчёт.

# Все задачи async. Timezone — Europe/Kyiv.

import logging
import httpx
from datetime import date, datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from models import (
get_session, get_or_create_user, get_today_report,
create_today_report, ShameLog, WeeklyStats,
XP_PENALTIES, get_level
)
from keyboards import kb_morning, kb_evening_report, kb_back_to_main
from content import get_law_of_day, get_quote_of_day

log = logging.getLogger(**name**)
TZ = ZoneInfo(“Europe/Kyiv”)

# День недели → тема изображения (Pollinations)

MORNING_THEMES = {
0: “majestic eagle soaring over dark city skyline, cinematic, power, minimal”,
1: “chess king piece dramatic lighting, strategy, black marble, 4k”,
2: “lone wolf standing on mountain peak, moonlight, epic, dark atmosphere”,
3: “glass skyscraper in fog, corporate power, minimalist, cold colors”,
4: “lion before hunt, intense eyes, savanna dusk, cinematic close-up”,
5: “blacksmith hammer striking hot iron, sparks, forge, dark dramatic”,
6: “ancient war map table, candles, strategy session, top view, moody”,
}

def escape_md(text: str) -> str:
chars = r”_*[]()~`>#+-=|{}.!”
for c in chars:
text = text.replace(c, f”\{c}”)
return text

# ─────────────────────────────────────────────

# POLLINATIONS — генерация изображения

# ─────────────────────────────────────────────

async def generate_morning_image(prompt: str, width: int = 1024, height: int = 576) -> bytes | None:
“””
Запрашивает изображение у Pollinations.ai.
Бесплатно, без ключей. Возвращает байты или None при ошибке.
“””
encoded = prompt.replace(” “, “%20”).replace(”,”, “%2C”)
url = f”https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true”

```
try:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        if response.status_code == 200:
            return response.content
except Exception as e:
    log.warning(f"Pollinations error: {e}")
return None
```

# ─────────────────────────────────────────────

# УТРЕННЕЕ УВЕДОМЛЕНИЕ — 07:00

# ─────────────────────────────────────────────

async def morning_push(bot: Bot, user_id: int, channel_id: int):
“””
07:00 — Картинка + закон дня + цитата.
Отправляется в личку пользователю и в канал.
“””
session = get_session()
user = get_or_create_user(session, telegram_id=user_id)
today = date.today()
weekday = today.weekday()

```
# Контент дня
law = get_law_of_day(user.last_law_index)
quote = get_quote_of_day(user.last_quote_index)
lvl = user.get_level_info()
session.close()

# Текст утреннего сообщения
day_names = ["ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ", "ПЯТНИЦА", "СУББОТА", "ВОСКРЕСЕНЬЕ"]
day_name = escape_md(day_names[weekday])
date_str = escape_md(today.strftime("%d.%m.%Y"))
law_title = escape_md(law["title"])
law_num = escape_md(str(law.get("number", "?")))
quote_text = escape_md(quote["text"])
quote_author = escape_md(quote["author"])
level_name = escape_md(lvl["name"])
bar = escape_md(user.get_progress_bar())
streak = user.streak

caption = (
    f"*⚡ {day_name} \\| {date_str}*\n"
    f"`{'═' * 26}`\n\n"
    f"*Статус:* `{level_name}`\n"
    f"*XP:* `{user.xp}` \\| 🔥 `{streak} дней`\n"
    f"`{bar}`\n\n"
    f"`{'─' * 26}`\n\n"
    f"*⚖️ ЗАКОН {law_num}:*\n"
    f"_{law_title}_\n\n"
    f">_{quote_text}_\n"
    f"— {quote_author}\n\n"
    f"`{'─' * 26}`\n"
    f"_Сегодня ты или работаешь, или оправдываешься\\. Третьего нет\\._"
)

# Генерируем картинку
theme = MORNING_THEMES.get(weekday, MORNING_THEMES[0])
image_bytes = await generate_morning_image(theme)

try:
    if image_bytes:
        from aiogram.types import BufferedInputFile
        photo = BufferedInputFile(image_bytes, filename="monarch_morning.jpg")
        await bot.send_photo(
            chat_id=user_id,
            photo=photo,
            caption=caption,
            parse_mode="MarkdownV2",
            reply_markup=kb_morning()
        )
        # В канал — без кнопок
        await bot.send_photo(
            chat_id=channel_id,
            photo=photo,
            caption=caption,
            parse_mode="MarkdownV2"
        )
    else:
        # Fallback: только текст если картинка не загрузилась
        await bot.send_message(user_id, caption, parse_mode="MarkdownV2", reply_markup=kb_morning())
        await bot.send_message(channel_id, caption, parse_mode="MarkdownV2")

except TelegramBadRequest as e:
    log.error(f"Morning push error: {e}")
```

# ─────────────────────────────────────────────

# НАПОМИНАНИЕ В ОБЕД — 12:00

# ─────────────────────────────────────────────

async def midday_check(bot: Bot, user_id: int):
“”“12:00 — короткий пинг. Без картинки.”””
session = get_session()
user = get_or_create_user(session, telegram_id=user_id)
today = date.today().isoformat()
report = get_today_report(session, user_id, today)
session.close()

```
# Если уже отмечено — не беспокоим
if report and report.q1_answered:
    return

streak = user.streak
streak_text = f"🔥 Серия: `{streak}` дней\\." if streak > 0 else "Серия обнулена\\."

text = (
    f"*📍 ПОЛДЕНЬ*\n"
    f"`─────────────────────`\n\n"
    f"{streak_text}\n\n"
    f"_Ты на треке?_\n"
    f"Вечером в 21:00 — отчёт\\."
)

try:
    await bot.send_message(user_id, text, parse_mode="MarkdownV2")
except TelegramBadRequest as e:
    log.error(f"Midday check error: {e}")
```

# ─────────────────────────────────────────────

# ВЕЧЕРНИЙ УЛЬТИМАТУМ — 21:00

# ─────────────────────────────────────────────

async def evening_report_push(bot: Bot, user_id: int):
“””
21:00 — Отправляет форму вечернего отчёта.
Сохраняет message_id для последующего edit.
“””
session = get_session()
user = get_or_create_user(session, telegram_id=user_id)
today = date.today().isoformat()
report = get_today_report(session, user_id, today)

```
if report and report.is_complete:
    session.close()
    return

q1 = report.q1_answered if report else False
q2 = report.q2_answered if report else False
q3 = report.q3_answered if report else False

text = (
    f"*🌑 ВЕЧЕРНИЙ ОТЧЁТ*\n"
    f"`{'════════════════════════'}`\n\n"
    f"21:00\\. Время отчитаться\\.\n"
    f"_У тебя 60 минут\\. После — автоштраф\\._\n\n"
    f"`────────────────────────`"
)

try:
    sent = await bot.send_message(
        user_id, text,
        parse_mode="MarkdownV2",
        reply_markup=kb_evening_report(q1, q2, q3)
    )
    if not report:
        create_today_report(session, user_id, today, message_id=sent.message_id)
    else:
        report.message_id = sent.message_id
    session.commit()
except TelegramBadRequest as e:
    log.error(f"Evening push error: {e}")

session.close()
```

# ─────────────────────────────────────────────

# АВТОШТРАФ — 22:00

# ─────────────────────────────────────────────

async def auto_penalty(bot: Bot, user_id: int, channel_id: int):
“””
22:00 — Если отчёт не сдан, снимаем XP и пишем в позорную доску.
“””
session = get_session()
user = get_or_create_user(session, telegram_id=user_id)
today = date.today().isoformat()
report = get_today_report(session, user_id, today)

```
if report and report.is_complete:
    session.close()
    return

# Штраф
penalty = XP_PENALTIES["no_report"]
user.apply_xp(penalty)

# Лог
shame = ShameLog(
    user_id=user_id,
    date=today,
    event_type="no_report",
    xp_lost=penalty,
)
session.add(shame)
session.commit()

xp_lost_display = abs(penalty)
text_user = (
    f"*⚠️ ОТЧЁТ НЕ СДАН*\n"
    f"`─────────────────────`\n\n"
    f"Автоштраф: `\\-{xp_lost_display} XP`\n"
    f"*Итого XP:* `{user.xp}`\n\n"
    f"_Молчание — тоже выбор\\. Трусливый\\._"
)

text_channel = (
    f"*🩸 НАРУШЕНИЕ ПРОТОКОЛА*\n"
    f"`{'═' * 26}`\n\n"
    f"`[{escape_md(today)}]` ОТЧЁТ ПРОПУЩЕН\n"
    f"ШТРАФ: `\\-{xp_lost_display} XP`\n"
    f"СТАТУС: `{escape_md(user.get_level_info()['name'])}`\n\n"
    f"`// Система зафиксировала отказ от отчётности`"
)

try:
    await bot.send_message(user_id, text_user, parse_mode="MarkdownV2")
    await bot.send_message(channel_id, text_channel, parse_mode="MarkdownV2")
except TelegramBadRequest as e:
    log.error(f"Auto penalty error: {e}")

session.close()
```

# ─────────────────────────────────────────────

# ЕЖЕНЕДЕЛЬНЫЙ ОТЧЁТ — воскресенье 20:00

# ─────────────────────────────────────────────

async def weekly_report(bot: Bot, user_id: int, channel_id: int):
“”“Воскресенье 20:00 — итоги недели в канал.”””
from models import DailyReport
session = get_session()
user = get_or_create_user(session, telegram_id=user_id)

```
today = date.today()
week_start = today.strftime("%Y-%m-%d")

# Берём отчёты за последние 7 дней
from datetime import timedelta
dates = [(today - timedelta(days=i)).isoformat() for i in range(7)]
reports = session.query(DailyReport).filter(
    DailyReport.user_id == user_id,
    DailyReport.date.in_(dates)
).all()

days_done = sum(1 for r in reports if r.plan_status == "done")
days_partial = sum(1 for r in reports if r.plan_status == "partial")
days_fail = sum(1 for r in reports if r.plan_status == "fail")
days_silent = 7 - len(reports)
clean_days = sum(1 for r in reports if r.dopamine_clean)

# XP за неделю из логов
from models import ShameLog
shame_logs = session.query(ShameLog).filter(
    ShameLog.user_id == user_id,
    ShameLog.date.in_(dates)
).all()
xp_lost = sum(abs(s.xp_lost) for s in shame_logs)

lvl = user.get_level_info()
bar = escape_md(user.get_progress_bar())

# Определяем вердикт
if days_done >= 6:
    verdict = "МОНАРХ НА ТРЕКЕ 🔥"
elif days_done >= 4:
    verdict = "ДЕРЖИШЬСЯ. НО МОЖЕШЬ ЛУЧШЕ."
elif days_done >= 2:
    verdict = "СЛАБАЯ НЕДЕЛЯ. ПОДТЯНИСЬ."
else:
    verdict = "ПРОВАЛ. НЕПРИЕМЛЕМО."

date_str = escape_md(today.strftime("%d.%m.%Y"))
lvl_name = escape_md(lvl["name"])

text = (
    f"*📊 ИТОГИ НЕДЕЛИ \\| {date_str}*\n"
    f"`{'═' * 28}`\n\n"
    f"*Уровень:* `{lvl_name}` \\| *XP:* `{user.xp}`\n"
    f"`{bar}`\n\n"
    f"`{'─' * 28}`\n\n"
    f"✅ Выполнено:   `{days_done}/7` дней\n"
    f"⚠️  Частично:   `{days_partial}` дней\n"
    f"💀 Слив:        `{days_fail}` дней\n"
    f"🔇 Молчание:    `{days_silent}` дней\n\n"
    f"🧘 Без мусора:  `{clean_days}/7` дней\n"
    f"🔥 Серия:       `{user.streak}` дней\n"
    f"📉 XP потеряно: `{xp_lost}`\n\n"
    f"`{'─' * 28}`\n\n"
    f"*ВЕРДИКТ:* _{escape_md(verdict)}_"
)

try:
    await bot.send_message(channel_id, text, parse_mode="MarkdownV2")
    await bot.send_message(user_id, text, parse_mode="MarkdownV2")
except TelegramBadRequest as e:
    log.error(f"Weekly report error: {e}")

session.close()
```

# ─────────────────────────────────────────────

# ИНИЦИАЛИЗАЦИЯ ПЛАНИРОВЩИКА

# ─────────────────────────────────────────────

def setup_scheduler(bot: Bot, user_id: int, channel_id: int) -> AsyncIOScheduler:
“””
Создаёт и возвращает настроенный планировщик.
Вызывается из main.py при старте.
“””
scheduler = AsyncIOScheduler(timezone=TZ)

```
# 07:00 — утреннее уведомление
scheduler.add_job(
    morning_push,
    CronTrigger(hour=7, minute=0, timezone=TZ),
    args=[bot, user_id, channel_id],
    id="morning_push",
    replace_existing=True,
)

# 12:00 — обеденный пинг
scheduler.add_job(
    midday_check,
    CronTrigger(hour=12, minute=0, timezone=TZ),
    args=[bot, user_id],
    id="midday_check",
    replace_existing=True,
)

# 21:00 — вечерний отчёт
scheduler.add_job(
    evening_report_push,
    CronTrigger(hour=21, minute=0, timezone=TZ),
    args=[bot, user_id],
    id="evening_report",
    replace_existing=True,
)

# 22:00 — автоштраф
scheduler.add_job(
    auto_penalty,
    CronTrigger(hour=22, minute=0, timezone=TZ),
    args=[bot, user_id, channel_id],
    id="auto_penalty",
    replace_existing=True,
)

# Воскресенье 20:00 — еженедельный отчёт
scheduler.add_job(
    weekly_report,
    CronTrigger(day_of_week="sun", hour=20, minute=0, timezone=TZ),
    args=[bot, user_id, channel_id],
    id="weekly_report",
    replace_existing=True,
)

return scheduler
```
