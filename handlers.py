# handlers.py — MONARCH BOT

# Вся логика команд и callback-обработчиков.

# aiogram 3.x — роутеры, FSM для Q3 отчёта.

import logging
from datetime import date, datetime, timezone

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from models import (
get_session, get_or_create_user, get_today_report,
create_today_report, ShameLog, WeeklyStats,
XP_REWARDS, XP_PENALTIES, get_level, get_next_level,
get_xp_progress_bar, LEVELS
)
from keyboards import (
kb_main_menu, kb_confirm_done, kb_confirm_fail,
kb_learn_menu, kb_content_card, kb_content_card_done,
kb_evening_report, kb_report_submitted,
kb_stats, kb_shame, kb_levelup, kb_back_to_main
)
from content import (
get_law_of_day, get_quote_of_day,
get_chapter_of_day, get_challenge_of_day,
LAWS, QUOTES, CHAPTERS, CHALLENGES
)

log = logging.getLogger(**name**)
router = Router()

# ─────────────────────────────────────────────

# FSM — состояния для Q3 отчёта (текстовый ввод)

# ─────────────────────────────────────────────

class ReportState(StatesGroup):
waiting_q3 = State()

# ─────────────────────────────────────────────

# УТИЛИТЫ

# ─────────────────────────────────────────────

def today_str() -> str:
return date.today().isoformat()

def escape_md(text: str) -> str:
“”“Экранирует спецсимволы для MarkdownV2.”””
chars = r”_*[]()~`>#+-=|{}.!”
for c in chars:
text = text.replace(c, f”\{c}”)
return text

def build_profile_text(user) -> str:
“”“Генерирует текст профиля в стиле приборной панели.”””
lvl = user.get_level_info()
next_lvl = get_next_level(user.xp)
bar = user.get_progress_bar()

```
next_info = f"{next_lvl['name']} \\({next_lvl['min_xp']} XP\\)" if next_lvl else "МАКСИМУМ"

streak_display = f"🔥 {user.streak}" if user.streak >= 3 else f"{user.streak}"

lines = [
    f"*{escape_md(lvl['emoji'])} MONARCH SYSTEM*",
    f"`{'─' * 28}`",
    f"",
    f"*СТАТУС:*  `{escape_md(lvl['name'])}`",
    f"*XP:*      `{user.xp}` pt",
    f"*ПРОГРЕСС:* `{escape_md(bar)}`",
    f"*СЛЕД\\.УРОВЕНЬ:* {next_info}",
    f"",
    f"`{'─' * 28}`",
    f"",
    f"🔥 *Серия:*     `{streak_display} дней`",
    f"📈 *Макс серия:* `{user.max_streak} дней`",
    f"",
    f"✅ *Выполнено:* `{user.total_done}` дней",
    f"💀 *Сливов:*    `{user.total_fails}`",
    f"📚 *Прочитано:* `{user.total_reads}` матер\\.",
    f"",
    f"`{'─' * 28}`",
]
return "\n".join(lines)
```

def build_shame_text(session, user_id: int) -> str:
“”“Генерирует текст позорной доски в стиле финансового лога.”””
logs = session.query(ShameLog).filter_by(user_id=user_id)  
.order_by(ShameLog.created_at.desc()).limit(10).all()

```
event_map = {
    "fail":         "ПРИЗНАН СЛИВ",
    "no_report":    "ОТЧЁТ ПРОПУЩЕН",
    "streak_break": "СЕРИЯ СОРВАНА",
}

lines = [
    f"*🩸 MONARCH \\| ДОСКА ПОЗОРА*",
    f"`{'═' * 28}`",
    f"",
]

if not logs:
    lines.append("`// ИСТОРИЯ ЧИСТА`")
else:
    for log_entry in logs:
        event = escape_md(event_map.get(log_entry.event_type, log_entry.event_type))
        xp_lost = abs(log_entry.xp_lost)
        date_str = escape_md(log_entry.date)
        lines.append(f"`[{date_str}]` \\|\\| {event} \\|\\| `\\-{xp_lost} XP`")

lines += [
    f"",
    f"`{'═' * 28}`",
]
return "\n".join(lines)
```

async def check_levelup(bot: Bot, user, old_xp: int, chat_id: int):
“”“Проверяет левел-ап и отправляет поздравление.”””
old_level = get_level(old_xp)
new_level = get_level(user.xp)

```
if new_level["name"] != old_level["name"]:
    text = (
        f"*⚡ НОВЫЙ УРОВЕНЬ*\n"
        f"`{'═' * 24}`\n\n"
        f"Ты достиг уровня\n"
        f"*{escape_md(new_level['emoji'])} {escape_md(new_level['name'])}*\n\n"
        f"`{escape_md(user.get_progress_bar())}`\n\n"
        f"_Власть не даётся\\. Она берётся\\._"
    )
    await bot.send_message(chat_id, text, parse_mode="MarkdownV2", reply_markup=kb_levelup())
```

# ─────────────────────────────────────────────

# /start — профиль + главное меню

# ─────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message):
session = get_session()
user = get_or_create_user(
session,
telegram_id=message.from_user.id,
username=message.from_user.username,
first_name=message.from_user.first_name,
)
session.commit()

```
text = build_profile_text(user)
session.close()

await message.answer(text, parse_mode="MarkdownV2", reply_markup=kb_main_menu())
```

# ─────────────────────────────────────────────

# CALLBACK: menu:main — вернуться в главное меню

# ─────────────────────────────────────────────

@router.callback_query(F.data == “menu:main”)
async def cb_main_menu(call: CallbackQuery):
session = get_session()
user = get_or_create_user(session, telegram_id=call.from_user.id)
text = build_profile_text(user)
session.close()

```
try:
    await call.message.edit_text(text, parse_mode="MarkdownV2", reply_markup=kb_main_menu())
except TelegramBadRequest:
    pass
await call.answer()
```

# ─────────────────────────────────────────────

# CALLBACK: action:done — выполнил план

# ─────────────────────────────────────────────

@router.callback_query(F.data == “action:done”)
async def cb_action_done_confirm(call: CallbackQuery):
today = today_str()
session = get_session()
report = get_today_report(session, call.from_user.id, today)
session.close()

```
if report and report.plan_status == "done":
    await call.answer("✅ Уже зафиксировано сегодня.", show_alert=True)
    return

text = (
    "*⚡ ПОДТВЕРЖДЕНИЕ*\n"
    "`─────────────────────────`\n\n"
    "Ты выполнил план на сегодня\\?\n\n"
    "_Это фиксируется\\._ Не ври себе\\."
)
try:
    await call.message.edit_text(text, parse_mode="MarkdownV2", reply_markup=kb_confirm_done())
except TelegramBadRequest:
    pass
await call.answer()
```

@router.callback_query(F.data == “confirm:done”)
async def cb_confirm_done(call: CallbackQuery, bot: Bot):
session = get_session()
user = get_or_create_user(session, telegram_id=call.from_user.id)
today = today_str()

```
old_xp = user.xp
streak_result = user.update_streak(today)
xp_gain = XP_REWARDS["done"]
bonus_text = ""

# Streak бонусы
if streak_result["status"] == "continued" or streak_result["status"] == "started":
    if user.streak == 7:
        xp_gain += XP_REWARDS["streak_7"]
        bonus_text = f"\n🔥 *БОНУС серии 7 дней\\!* `\\+{XP_REWARDS['streak_7']} XP`"
    elif user.streak == 30:
        xp_gain += XP_REWARDS["streak_30"]
        bonus_text = f"\n🔥 *БОНУС серии 30 дней\\!* `\\+{XP_REWARDS['streak_30']} XP`"

user.apply_xp(xp_gain)
user.total_done += 1

# Отчёт дня
report = get_today_report(session, call.from_user.id, today)
if not report:
    report = create_today_report(session, call.from_user.id, today)
report.plan_status = "done"
report.q1_answered = True

session.commit()

streak_emoji = "🔥" if user.streak >= 3 else "✅"
text = (
    f"*✅ ПЛАН ВЫПОЛНЕН*\n"
    f"`{'─' * 24}`\n\n"
    f"*\\+{xp_gain} XP* начислено{bonus_text}\n\n"
    f"{streak_emoji} *Серия:* `{user.streak} дней`\n"
    f"*Всего XP:* `{user.xp}`\n"
    f"`{escape_md(user.get_progress_bar())}`"
)

try:
    await call.message.edit_text(text, parse_mode="MarkdownV2", reply_markup=kb_main_menu())
except TelegramBadRequest:
    pass

await check_levelup(bot, user, old_xp, call.message.chat.id)
session.close()
await call.answer("✅ Зафиксировано.")
```

# ─────────────────────────────────────────────

# CALLBACK: action:fail — слив

# ─────────────────────────────────────────────

@router.callback_query(F.data == “action:fail”)
async def cb_action_fail_confirm(call: CallbackQuery):
text = (
“*💀 ПРИЗНАНИЕ СЛИВА*\n”
“`─────────────────────────`\n\n”
“Это стоит `20 XP`\.\n\n”
“*Честность — единственная валюта здесь\.*\n”
“Подтверди\.”
)
try:
await call.message.edit_text(text, parse_mode=“MarkdownV2”, reply_markup=kb_confirm_fail())
except TelegramBadRequest:
pass
await call.answer()

@router.callback_query(F.data == “confirm:fail”)
async def cb_confirm_fail(call: CallbackQuery, bot: Bot):
session = get_session()
user = get_or_create_user(session, telegram_id=call.from_user.id)
today = today_str()

```
old_xp = user.xp
penalty = XP_PENALTIES["fail"]
user.apply_xp(penalty)
user.total_fails += 1

# Сброс streak
streak_broke = user.streak > 1
if streak_broke:
    lost_streak = user.streak
    user.streak = 0
    user.last_done_date = None

# Лог позорной доски
shame = ShameLog(
    user_id=call.from_user.id,
    date=today,
    event_type="fail",
    xp_lost=penalty,
)
session.add(shame)

# Отчёт дня
report = get_today_report(session, call.from_user.id, today)
if not report:
    report = create_today_report(session, call.from_user.id, today)
report.plan_status = "fail"
report.q1_answered = True

session.commit()

streak_text = f"\n💀 *Серия сброшена\\!* Было `{lost_streak}` дней\\." if streak_broke else ""

text = (
    f"*💀 СЛИВ ЗАФИКСИРОВАН*\n"
    f"`{'─' * 24}`\n\n"
    f"*{penalty} XP* снято{streak_text}\n\n"
    f"*Осталось XP:* `{user.xp}`\n"
    f"`{escape_md(user.get_progress_bar())}`\n\n"
    f"_Слабость признана\\. Теперь работай\\._"
)

try:
    await call.message.edit_text(text, parse_mode="MarkdownV2", reply_markup=kb_main_menu())
except TelegramBadRequest:
    pass

session.close()
await call.answer("💀 Зафиксировано.")
```

@router.callback_query(F.data == “confirm:cancel”)
async def cb_cancel(call: CallbackQuery):
session = get_session()
user = get_or_create_user(session, telegram_id=call.from_user.id)
text = build_profile_text(user)
session.close()

```
try:
    await call.message.edit_text(text, parse_mode="MarkdownV2", reply_markup=kb_main_menu())
except TelegramBadRequest:
    pass
await call.answer()
```

# ─────────────────────────────────────────────

# CALLBACK: learn:menu — меню учёбы

# ─────────────────────────────────────────────

@router.callback_query(F.data == “learn:menu”)
async def cb_learn_menu(call: CallbackQuery):
text = (
“*📚 БЛОК ЗНАНИЙ*\n”
“`─────────────────────────`\n\n”
“Выбери формат\:\n\n”
“⚖️  *Закон дня* — Роберт Грин\n”
“💬 *Цитата* — предприниматели\n”
“📖 *Глава* — Сунь\-Цзи / Мангер\n”
“🎯 *Задача* — бизнес\-кейс”
)
try:
await call.message.edit_text(text, parse_mode=“MarkdownV2”, reply_markup=kb_learn_menu())
except TelegramBadRequest:
pass
await call.answer()

# ─────────────────────────────────────────────

# CALLBACK: learn:law / quote / chapter / challenge

# ─────────────────────────────────────────────

@router.callback_query(F.data == “learn:law”)
async def cb_learn_law(call: CallbackQuery):
session = get_session()
user = get_or_create_user(session, telegram_id=call.from_user.id)
idx = user.last_law_index % len(LAWS)
law = LAWS[idx]
session.close()

```
num = escape_md(str(law.get("number", idx + 1)))
title = escape_md(law["title"])
body = escape_md(law["body"])
lesson = escape_md(law.get("lesson", ""))

text = (
    f"*⚖️ ЗАКОН {num}*\n"
    f"`{'═' * 26}`\n\n"
    f"*{title}*\n\n"
    f"||{body}||\n\n"
    f"_💡 Вывод: {lesson}_"
)
try:
    await call.message.edit_text(
        text, parse_mode="MarkdownV2",
        reply_markup=kb_content_card("law", idx)
    )
except TelegramBadRequest:
    pass
await call.answer()
```

@router.callback_query(F.data == “learn:quote”)
async def cb_learn_quote(call: CallbackQuery):
session = get_session()
user = get_or_create_user(session, telegram_id=call.from_user.id)
idx = user.last_quote_index % len(QUOTES)
q = QUOTES[idx]
session.close()

```
author = escape_md(q["author"])
text_q = escape_md(q["text"])
context = escape_md(q.get("context", ""))

text = (
    f"*💬 ЦИТАТА*\n"
    f"`{'═' * 26}`\n\n"
    f">_{text_q}_\n\n"
    f"— *{author}*\n\n"
    f"||{context}||"
)
try:
    await call.message.edit_text(
        text, parse_mode="MarkdownV2",
        reply_markup=kb_content_card("quote", idx)
    )
except TelegramBadRequest:
    pass
await call.answer()
```

@router.callback_query(F.data == “learn:chapter”)
async def cb_learn_chapter(call: CallbackQuery):
session = get_session()
user = get_or_create_user(session, telegram_id=call.from_user.id)
idx = user.last_chapter_index % len(CHAPTERS)
ch = CHAPTERS[idx]
session.close()

```
source = escape_md(ch["source"])
title = escape_md(ch["title"])
body = escape_md(ch["body"])
question = escape_md(ch.get("question", "Что ты возьмёшь из этого?"))

text = (
    f"*📖 ГЛАВА ДНЯ*\n"
    f"`{'═' * 26}`\n"
    f"_{source}_\n\n"
    f"*{title}*\n\n"
    f"||{body}||\n\n"
    f"🤔 *Вопрос:* {question}"
)
try:
    await call.message.edit_text(
        text, parse_mode="MarkdownV2",
        reply_markup=kb_content_card("chapter", idx)
    )
except TelegramBadRequest:
    pass
await call.answer()
```

@router.callback_query(F.data == “learn:challenge”)
async def cb_learn_challenge(call: CallbackQuery):
session = get_session()
user = get_or_create_user(session, telegram_id=call.from_user.id)
idx = user.last_challenge_index % len(CHALLENGES)
ch = CHALLENGES[idx]
session.close()

```
title = escape_md(ch["title"])
task = escape_md(ch["task"])
answer = escape_md(ch.get("answer", "Нет универсального ответа. Думай сам."))

text = (
    f"*🎯 ЗАДАЧА*\n"
    f"`{'═' * 26}`\n\n"
    f"*{title}*\n\n"
    f"{task}\n\n"
    f"||💡 Разбор: {answer}||"
)
try:
    await call.message.edit_text(
        text, parse_mode="MarkdownV2",
        reply_markup=kb_content_card("challenge", idx)
    )
except TelegramBadRequest:
    pass
await call.answer()
```

# ─────────────────────────────────────────────

# CALLBACK: learned:<type>:<idx> — засчитать XP за контент

# ─────────────────────────────────────────────

@router.callback_query(F.data.startswith(“learned:”))
async def cb_learned(call: CallbackQuery, bot: Bot):
_, content_type, idx_str = call.data.split(”:”)
idx = int(idx_str)

```
session = get_session()
user = get_or_create_user(session, telegram_id=call.from_user.id)
old_xp = user.xp

# Продвигаем индекс контента вперёд
index_map = {
    "law":       "last_law_index",
    "quote":     "last_quote_index",
    "chapter":   "last_chapter_index",
    "challenge": "last_challenge_index",
}
attr = index_map.get(content_type)
if attr:
    current = getattr(user, attr)
    if current == idx:   # не засчитывали ещё
        setattr(user, attr, idx + 1)
        xp = XP_REWARDS["challenge"] if content_type == "challenge" else XP_REWARDS["read"]
        user.apply_xp(xp)
        user.total_reads += 1
        session.commit()
        await call.answer(f"+{xp} XP начислено ✅")
    else:
        await call.answer("Уже засчитано.", show_alert=False)
else:
    await call.answer()

# Меняем кнопку на "✓ XP начислен"
try:
    await call.message.edit_reply_markup(
        reply_markup=kb_content_card_done(content_type)
    )
except TelegramBadRequest:
    pass

await check_levelup(bot, user, old_xp, call.message.chat.id)
session.close()
```

# ─────────────────────────────────────────────

# /report — ручной вечерний отчёт

# ─────────────────────────────────────────────

@router.message(Command(“report”))
async def cmd_report(message: Message):
today = today_str()
session = get_session()
user = get_or_create_user(session, telegram_id=message.from_user.id)
report = get_today_report(session, message.from_user.id, today)

```
if report and report.is_complete:
    session.close()
    await message.answer(
        "*✅ Отчёт сегодня уже сдан\\.*",
        parse_mode="MarkdownV2",
        reply_markup=kb_back_to_main()
    )
    return

q1 = report.q1_answered if report else False
q2 = report.q2_answered if report else False
q3 = report.q3_answered if report else False

text = _report_header_text()
sent = await message.answer(
    text, parse_mode="MarkdownV2",
    reply_markup=kb_evening_report(q1, q2, q3)
)

if not report:
    create_today_report(session, message.from_user.id, today, message_id=sent.message_id)
else:
    report.message_id = sent.message_id
session.commit()
session.close()
```

def _report_header_text() -> str:
return (
“*📋 ВЕЧЕРНИЙ ОТЧЁТ*\n”
“`════════════════════════`\n\n”
“Ответь на три вопроса\.\n”
“*Честно\. Без самообмана\.*\n\n”
“`────────────────────────`”
)

# ─────────────────────────────────────────────

# CALLBACK: report:q1 — вопрос о плане

# ─────────────────────────────────────────────

@router.callback_query(F.data.startswith(“report:q1:”))
async def cb_report_q1(call: CallbackQuery):
answer = call.data.split(”:”)[-1]   # done | partial | fail
today = today_str()

```
session = get_session()
report = get_today_report(session, call.from_user.id, today)
if not report:
    report = create_today_report(session, call.from_user.id, today, call.message.message_id)

if report.q1_answered:
    await call.answer("Уже отмечено.", show_alert=False)
    session.close()
    return

report.plan_status = answer
report.q1_answered = True
session.commit()

try:
    await call.message.edit_reply_markup(
        reply_markup=kb_evening_report(True, report.q2_answered, report.q3_answered)
    )
except TelegramBadRequest:
    pass

answer_label = {"done": "Выполнен ✅", "partial": "Частично ⚠️", "fail": "Слив 💀"}
await call.answer(answer_label.get(answer, "Принято"))
session.close()
```

# ─────────────────────────────────────────────

# CALLBACK: report:q2 — вопрос о дофамине

# ─────────────────────────────────────────────

@router.callback_query(F.data.startswith(“report:q2:”))
async def cb_report_q2(call: CallbackQuery):
answer = call.data.split(”:”)[-1]   # clean | fail
today = today_str()

```
session = get_session()
report = get_today_report(session, call.from_user.id, today)
if not report:
    report = create_today_report(session, call.from_user.id, today, call.message.message_id)

if report.q2_answered:
    await call.answer("Уже отмечено.", show_alert=False)
    session.close()
    return

report.dopamine_clean = (answer == "clean")
report.q2_answered = True
session.commit()

try:
    await call.message.edit_reply_markup(
        reply_markup=kb_evening_report(report.q1_answered, True, report.q3_answered)
    )
except TelegramBadRequest:
    pass

await call.answer("Чисто ✅" if answer == "clean" else "Отмечено 💀")
session.close()
```

# ─────────────────────────────────────────────

# CALLBACK: report:q3:prompt — запрос текста Q3

# ─────────────────────────────────────────────

@router.callback_query(F.data == “report:q3:prompt”)
async def cb_report_q3_prompt(call: CallbackQuery, state: FSMContext):
today = today_str()
session = get_session()
report = get_today_report(session, call.from_user.id, today)
session.close()

```
if report and report.q3_answered:
    await call.answer("Уже отмечено.", show_alert=False)
    return

await state.set_state(ReportState.waiting_q3)
await state.update_data(
    report_msg_id=call.message.message_id,
    report_chat_id=call.message.chat.id
)

await call.message.answer(
    "*✍️ Напиши одно действие*\n"
    "_Что ты сделал сегодня для своего будущего?_\n\n"
    "`Минимум 20 символов\\. Без воды\\.`",
    parse_mode="MarkdownV2"
)
await call.answer()
```

@router.message(ReportState.waiting_q3)
async def process_q3_text(message: Message, state: FSMContext, bot: Bot):
text = message.text or “”

```
if len(text) < 20:
    await message.answer(
        "⚠️ *Слишком коротко\\.*\n_Минимум 20 символов\\. Что конкретно ты сделал?_",
        parse_mode="MarkdownV2"
    )
    return

data = await state.get_data()
today = today_str()

session = get_session()
report = get_today_report(session, message.from_user.id, today)
if not report:
    report = create_today_report(session, message.from_user.id, today)

report.future_action = text
report.q3_answered = True
session.commit()

await state.clear()

# Редактируем оригинальное сообщение отчёта
try:
    await bot.edit_message_reply_markup(
        chat_id=data["report_chat_id"],
        message_id=data["report_msg_id"],
        reply_markup=kb_evening_report(report.q1_answered, report.q2_answered, True)
    )
except TelegramBadRequest:
    pass

await message.answer(
    "✅ *Принято\\.*",
    parse_mode="MarkdownV2"
)
session.close()
```

# ─────────────────────────────────────────────

# CALLBACK: report:submit — финальная отправка

# ─────────────────────────────────────────────

@router.callback_query(F.data == “report:submit”)
async def cb_report_submit(call: CallbackQuery, bot: Bot):
today = today_str()
session = get_session()
user = get_or_create_user(session, telegram_id=call.from_user.id)
report = get_today_report(session, call.from_user.id, today)

```
if not report or not (report.q1_answered and report.q2_answered and report.q3_answered):
    await call.answer("Ответь на все вопросы сначала.", show_alert=True)
    session.close()
    return

if report.is_complete:
    await call.answer("Уже отправлено.", show_alert=False)
    session.close()
    return

old_xp = user.xp
xp = XP_REWARDS["report"]
user.apply_xp(xp)
report.is_complete = True
report.xp_awarded = xp
session.commit()

plan_emoji = {"done": "✅", "partial": "⚠️", "fail": "💀"}.get(report.plan_status, "—")
dopamine_emoji = "✅" if report.dopamine_clean else "💀"
action_text = escape_md(report.future_action or "—")

summary = (
    f"*✅ ОТЧЁТ ПРИНЯТ*\n"
    f"`{'═' * 24}`\n\n"
    f"План: {plan_emoji}   Мусор: {dopamine_emoji}\n"
    f"Действие: _{action_text}_\n\n"
    f"*\\+{xp} XP* за честность\\.\n"
    f"*Итого:* `{user.xp} XP`"
)

try:
    await call.message.edit_text(
        summary, parse_mode="MarkdownV2",
        reply_markup=kb_report_submitted()
    )
except TelegramBadRequest:
    pass

await check_levelup(bot, user, old_xp, call.message.chat.id)
session.close()
await call.answer("✅ Отчёт сдан.")
```

# ─────────────────────────────────────────────

# CALLBACK: stats — статистика

# ─────────────────────────────────────────────

@router.callback_query(F.data.startswith(“stats:”))
async def cb_stats(call: CallbackQuery):
session = get_session()
user = get_or_create_user(session, telegram_id=call.from_user.id)

```
total = user.total_done + user.total_fails
win_rate = int((user.total_done / total * 100)) if total > 0 else 0
lvl = user.get_level_info()

text = (
    f"*📊 СТАТИСТИКА*\n"
    f"`{'═' * 26}`\n\n"
    f"*Уровень:* `{escape_md(lvl['name'])}`\n"
    f"*XP:* `{user.xp}` \\| Макс: `{user.total_xp_earned}`\n"
    f"`{escape_md(user.get_progress_bar())}`\n\n"
    f"`{'─' * 26}`\n\n"
    f"🔥 Серия: `{user.streak}` дней\n"
    f"🏆 Рекорд: `{user.max_streak}` дней\n\n"
    f"✅ Выполнено: `{user.total_done}` дней\n"
    f"💀 Сливов: `{user.total_fails}`\n"
    f"📈 KPI: `{win_rate}%`\n\n"
    f"📚 Изучено: `{user.total_reads}` материалов\n"
)
session.close()

try:
    await call.message.edit_text(text, parse_mode="MarkdownV2", reply_markup=kb_stats())
except TelegramBadRequest:
    pass
await call.answer()
```

# ─────────────────────────────────────────────

# CALLBACK: shame:show — позорная доска

# ─────────────────────────────────────────────

@router.callback_query(F.data == “shame:show”)
async def cb_shame(call: CallbackQuery):
session = get_session()
text = build_shame_text(session, call.from_user.id)
session.close()

```
try:
    await call.message.edit_text(text, parse_mode="MarkdownV2", reply_markup=kb_shame())
except TelegramBadRequest:
    pass
await call.answer()
```

# ─────────────────────────────────────────────

# CALLBACK: /shame команда

# ─────────────────────────────────────────────

@router.message(Command(“shame”))
async def cmd_shame(message: Message):
session = get_session()
text = build_shame_text(session, message.from_user.id)
session.close()
await message.answer(text, parse_mode=“MarkdownV2”, reply_markup=kb_shame())

# ─────────────────────────────────────────────

# noop — заглушка для уже нажатых кнопок

# ─────────────────────────────────────────────

@router.callback_query(F.data == “noop”)
async def cb_noop(call: CallbackQuery):
await call.answer()
