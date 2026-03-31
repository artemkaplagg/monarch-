# keyboards.py — MONARCH BOT

# Все клавиатуры. Плиточный UI. Динамические состояния.

from aiogram.types import (
InlineKeyboardMarkup, InlineKeyboardButton,
ReplyKeyboardMarkup, KeyboardButton,
ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# ─────────────────────────────────────────────

# ГЛАВНОЕ МЕНЮ — “Приборная панель”

# Вызывается через /start. Показывает статус.

# ─────────────────────────────────────────────

def kb_main_menu() -> InlineKeyboardMarkup:
builder = InlineKeyboardBuilder()

```
builder.row(
    InlineKeyboardButton(text="⚡ ВЫПОЛНИЛ ПЛАН",    callback_data="action:done"),
    InlineKeyboardButton(text="💀 СЛИВ",              callback_data="action:fail"),
)
builder.row(
    InlineKeyboardButton(text="📚 УЧЁБА",             callback_data="learn:menu"),
    InlineKeyboardButton(text="📊 СТАТИСТИКА",        callback_data="stats:week"),
)
builder.row(
    InlineKeyboardButton(text="🩸 ПОЗОРНАЯ ДОСКА",    callback_data="shame:show"),
)

return builder.as_markup()
```

# ─────────────────────────────────────────────

# ПОДТВЕРЖДЕНИЕ ДЕЙСТВИЙ

# ─────────────────────────────────────────────

def kb_confirm_done() -> InlineKeyboardMarkup:
builder = InlineKeyboardBuilder()
builder.row(
InlineKeyboardButton(text=“✅ Подтвердить”,   callback_data=“confirm:done”),
InlineKeyboardButton(text=“✗ Отмена”,         callback_data=“confirm:cancel”),
)
return builder.as_markup()

def kb_confirm_fail() -> InlineKeyboardMarkup:
builder = InlineKeyboardBuilder()
builder.row(
InlineKeyboardButton(text=“💀 Признать слив”, callback_data=“confirm:fail”),
InlineKeyboardButton(text=“✗ Отмена”,         callback_data=“confirm:cancel”),
)
return builder.as_markup()

# ─────────────────────────────────────────────

# МЕНЮ ОБУЧЕНИЯ — /learn

# ─────────────────────────────────────────────

def kb_learn_menu() -> InlineKeyboardMarkup:
builder = InlineKeyboardBuilder()

```
builder.row(
    InlineKeyboardButton(text="⚖️  Закон дня",       callback_data="learn:law"),
    InlineKeyboardButton(text="💬 Цитата",            callback_data="learn:quote"),
)
builder.row(
    InlineKeyboardButton(text="📖 Глава дня",        callback_data="learn:chapter"),
    InlineKeyboardButton(text="🎯 Задача",            callback_data="learn:challenge"),
)
builder.row(
    InlineKeyboardButton(text="← Назад",             callback_data="menu:main"),
)

return builder.as_markup()
```

def kb_content_card(content_type: str, content_id: int) -> InlineKeyboardMarkup:
“””
Кнопка под карточкой контента.
content_type: “law”|“quote”|“chapter”|“challenge”
“””
builder = InlineKeyboardBuilder()
builder.row(
InlineKeyboardButton(
text=“✅ Усвоено  +5 XP”,
callback_data=f”learned:{content_type}:{content_id}”
)
)
builder.row(
InlineKeyboardButton(text=“← К меню учёбы”, callback_data=“learn:menu”),
)
return builder.as_markup()

def kb_content_card_done(content_type: str) -> InlineKeyboardMarkup:
“”“Кнопка после нажатия ‘Усвоено’ — уже нажата, заменяет предыдущую.”””
builder = InlineKeyboardBuilder()
builder.row(
InlineKeyboardButton(text=“✓ XP начислен”,  callback_data=“noop”),
)
builder.row(
InlineKeyboardButton(text=“← К меню учёбы”, callback_data=“learn:menu”),
)
return builder.as_markup()

# ─────────────────────────────────────────────

# ВЕЧЕРНИЙ ОТЧЁТ — динамические чекбоксы

# Сообщение редактируется, не переотправляется.

# ─────────────────────────────────────────────

def kb_evening_report(q1: bool = False, q2: bool = False, q3: bool = False) -> InlineKeyboardMarkup:
“””
Динамические кнопки отчёта.
При нажатии — [ ] меняется на [✅] через edit_message.
“””
def check(answered: bool) -> str:
return “✅” if answered else “☐”

```
builder = InlineKeyboardBuilder()

# Q1 — план выполнен?
if not q1:
    builder.row(
        InlineKeyboardButton(text=f"{check(q1)} Выполнил план",    callback_data="report:q1:done"),
        InlineKeyboardButton(text="Частично",                       callback_data="report:q1:partial"),
        InlineKeyboardButton(text="Слил",                           callback_data="report:q1:fail"),
    )
else:
    builder.row(
        InlineKeyboardButton(text="✅ План — отмечено",             callback_data="noop"),
    )

# Q2 — без дофамина?
if not q2:
    builder.row(
        InlineKeyboardButton(text=f"{check(q2)} Без мусора",        callback_data="report:q2:clean"),
        InlineKeyboardButton(text="Сорвался",                       callback_data="report:q2:fail"),
    )
else:
    builder.row(
        InlineKeyboardButton(text="✅ Дофамин — отмечено",          callback_data="noop"),
    )

# Q3 — текстовый ответ (отдельная кнопка, открывает ввод)
if not q3:
    builder.row(
        InlineKeyboardButton(
            text=f"{check(q3)} Что сделал для будущего?",
            callback_data="report:q3:prompt"
        )
    )
else:
    builder.row(
        InlineKeyboardButton(text="✅ Действие — отмечено",         callback_data="noop"),
    )

# Кнопка отправки — появляется только когда все три ответа даны
if q1 and q2 and q3:
    builder.row(
        InlineKeyboardButton(text="🚀 ОТПРАВИТЬ ОТЧЁТ  +5 XP",     callback_data="report:submit"),
    )

return builder.as_markup()
```

def kb_report_submitted() -> InlineKeyboardMarkup:
“”“Кнопки после отправки отчёта.”””
builder = InlineKeyboardBuilder()
builder.row(
InlineKeyboardButton(text=“✓ Отчёт принят”,     callback_data=“noop”),
)
builder.row(
InlineKeyboardButton(text=“← Главное меню”,     callback_data=“menu:main”),
)
return builder.as_markup()

# ─────────────────────────────────────────────

# СТАТИСТИКА

# ─────────────────────────────────────────────

def kb_stats() -> InlineKeyboardMarkup:
builder = InlineKeyboardBuilder()
builder.row(
InlineKeyboardButton(text=“📅 За неделю”,   callback_data=“stats:week”),
InlineKeyboardButton(text=“📆 За месяц”,    callback_data=“stats:month”),
)
builder.row(
InlineKeyboardButton(text=“🔥 Streak”,      callback_data=“stats:streak”),
InlineKeyboardButton(text=“🩸 Провалы”,     callback_data=“stats:fails”),
)
builder.row(
InlineKeyboardButton(text=“← Назад”,        callback_data=“menu:main”),
)
return builder.as_markup()

# ─────────────────────────────────────────────

# ПОЗОРНАЯ ДОСКА

# ─────────────────────────────────────────────

def kb_shame() -> InlineKeyboardMarkup:
builder = InlineKeyboardBuilder()
builder.row(
InlineKeyboardButton(text=“← Закрыть”,     callback_data=“menu:main”),
)
return builder.as_markup()

# ─────────────────────────────────────────────

# УВЕДОМЛЕНИЕ ОБ УРОВНЕ (левел-ап)

# ─────────────────────────────────────────────

def kb_levelup() -> InlineKeyboardMarkup:
builder = InlineKeyboardBuilder()
builder.row(
InlineKeyboardButton(text=“⚡ Продолжить”,  callback_data=“menu:main”),
)
return builder.as_markup()

# ─────────────────────────────────────────────

# УТРЕННЕЕ УВЕДОМЛЕНИЕ

# ─────────────────────────────────────────────

def kb_morning() -> InlineKeyboardMarkup:
builder = InlineKeyboardBuilder()
builder.row(
InlineKeyboardButton(text=“⚡ НАЧАТЬ ДЕНЬ”, callback_data=“action:done”),
InlineKeyboardButton(text=“📚 Закон дня”,   callback_data=“learn:law”),
)
return builder.as_markup()

# ─────────────────────────────────────────────

# ВСПОМОГАТЕЛЬНЫЕ

# ─────────────────────────────────────────────

def kb_back_to_main() -> InlineKeyboardMarkup:
builder = InlineKeyboardBuilder()
builder.row(
InlineKeyboardButton(text=“← Главное меню”, callback_data=“menu:main”),
)
return builder.as_markup()

def kb_remove() -> ReplyKeyboardRemove:
“”“Убирает Reply-клавиатуру.”””
return ReplyKeyboardRemove()
