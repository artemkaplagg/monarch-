# models.py — MONARCH BOT

# SQLAlchemy + SQLite. Один пользователь. Без лишнего.

from sqlalchemy import (
create_engine, Column, Integer, String,
Boolean, DateTime, Text, Float
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone

Base = declarative_base()
engine = create_engine(“sqlite:///monarch.db”, echo=False)
Session = sessionmaker(bind=engine)

# ─────────────────────────────────────────────

# УРОВНИ ВЛАСТИ

# ─────────────────────────────────────────────

LEVELS = [
{“name”: “НОВОБРАНЕЦ”,  “min_xp”: 0,    “emoji”: “⬜”},
{“name”: “УЧЕНИК”,      “min_xp”: 100,  “emoji”: “🟦”},
{“name”: “СТРАТЕГ”,     “min_xp”: 300,  “emoji”: “🟨”},
{“name”: “ХИЩНИК”,      “min_xp”: 700,  “emoji”: “🟧”},
{“name”: “MONARCH”,     “min_xp”: 1500, “emoji”: “🟥”},
]

XP_REWARDS = {
“done”:          10,   # выполнил план
“read”:           5,   # прочитал материал
“report”:         5,   # заполнил вечерний отчёт
“streak_7”:      50,   # бонус за 7-дневную серию
“streak_30”:    200,   # бонус за 30-дневную серию
“challenge”:     15,   # решил задачу
}

XP_PENALTIES = {
“fail”:         -20,   # признал слив
“no_report”:    -10,   # не заполнил отчёт до 22:00
“streak_break”:  -5,   # сломал серию
}

def get_level(xp: int) -> dict:
“”“Возвращает текущий уровень по XP.”””
current = LEVELS[0]
for lvl in LEVELS:
if xp >= lvl[“min_xp”]:
current = lvl
return current

def get_next_level(xp: int) -> dict | None:
“”“Возвращает следующий уровень или None если MONARCH.”””
current = get_level(xp)
idx = next((i for i, l in enumerate(LEVELS) if l[“name”] == current[“name”]), 0)
if idx + 1 < len(LEVELS):
return LEVELS[idx + 1]
return None

def get_xp_progress_bar(xp: int, length: int = 10) -> str:
“”“Генерирует ASCII прогресс-бар XP.”””
current = get_level(xp)
next_lvl = get_next_level(xp)

```
if not next_lvl:
    return "█" * length + " MAX"

lvl_xp = xp - current["min_xp"]
lvl_total = next_lvl["min_xp"] - current["min_xp"]
percent = min(lvl_xp / lvl_total, 1.0)
filled = int(percent * length)
bar = "█" * filled + "░" * (length - filled)
return f"{bar} {int(percent * 100)}%"
```

# ─────────────────────────────────────────────

# МОДЕЛИ

# ─────────────────────────────────────────────

class User(Base):
“”“Основная модель пользователя.”””
**tablename** = “users”

```
id              = Column(Integer, primary_key=True)
telegram_id     = Column(Integer, unique=True, nullable=False)
username        = Column(String(64), nullable=True)
first_name      = Column(String(64), nullable=True)

# XP и уровень
xp              = Column(Integer, default=0)
total_xp_earned = Column(Integer, default=0)   # исторический максимум (без штрафов)

# Streak
streak          = Column(Integer, default=0)
max_streak      = Column(Integer, default=0)
last_done_date  = Column(String(10), nullable=True)   # "YYYY-MM-DD"

# Статистика
total_done      = Column(Integer, default=0)
total_fails     = Column(Integer, default=0)
total_reads     = Column(Integer, default=0)

# Контент — какой материал выдавали последним
last_law_index       = Column(Integer, default=0)
last_quote_index     = Column(Integer, default=0)
last_chapter_index   = Column(Integer, default=0)
last_challenge_index = Column(Integer, default=0)

# Даты
created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))
updated_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))

def apply_xp(self, amount: int) -> int:
    """Применяет XP изменение. Возвращает новое значение XP."""
    self.xp = max(0, self.xp + amount)
    if amount > 0:
        self.total_xp_earned += amount
    return self.xp

def update_streak(self, today: str) -> dict:
    """
    Обновляет streak. today — строка 'YYYY-MM-DD'.
    Возвращает dict: {"status": "continued"|"started"|"broken", "streak": int}
    """
    from datetime import date, timedelta

    if self.last_done_date is None:
        self.streak = 1
        self.last_done_date = today
        status = "started"
    else:
        last = date.fromisoformat(self.last_done_date)
        today_date = date.fromisoformat(today)
        delta = (today_date - last).days

        if delta == 1:
            self.streak += 1
            self.last_done_date = today
            status = "continued"
        elif delta == 0:
            status = "continued"   # уже зафиксировано сегодня
        else:
            self.streak = 1
            self.last_done_date = today
            status = "broken"

    if self.streak > self.max_streak:
        self.max_streak = self.streak

    return {"status": status, "streak": self.streak}

def get_level_info(self) -> dict:
    return get_level(self.xp)

def get_progress_bar(self) -> str:
    return get_xp_progress_bar(self.xp)

def __repr__(self):
    return f"<User {self.first_name} | XP:{self.xp} | Streak:{self.streak}>"
```

class DailyReport(Base):
“”“Вечерний отчёт пользователя.”””
**tablename** = “daily_reports”

```
id              = Column(Integer, primary_key=True)
user_id         = Column(Integer, nullable=False)
date            = Column(String(10), nullable=False)   # "YYYY-MM-DD"

# Три вопроса отчёта
plan_status     = Column(String(20), nullable=True)    # "done" | "partial" | "fail"
dopamine_clean  = Column(Boolean, nullable=True)       # True = без TikTok/мусора
future_action   = Column(Text, nullable=True)          # текстовый ответ

# Состояние заполнения (для динамических кнопок)
q1_answered     = Column(Boolean, default=False)
q2_answered     = Column(Boolean, default=False)
q3_answered     = Column(Boolean, default=False)
is_complete     = Column(Boolean, default=False)

# ID сообщения для edit (динамическое обновление без переотправки)
message_id      = Column(Integer, nullable=True)

xp_awarded      = Column(Integer, default=0)
created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))

def completion_percent(self) -> int:
    answered = sum([self.q1_answered, self.q2_answered, self.q3_answered])
    return int((answered / 3) * 100)

def __repr__(self):
    return f"<Report {self.date} | {self.completion_percent()}%>"
```

class ShameLog(Base):
“”“Лог позорной доски.”””
**tablename** = “shame_logs”

```
id          = Column(Integer, primary_key=True)
user_id     = Column(Integer, nullable=False)
date        = Column(String(10), nullable=False)
event_type  = Column(String(30), nullable=False)   # "fail"|"no_report"|"streak_break"
xp_lost     = Column(Integer, default=0)
note        = Column(Text, nullable=True)
created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

class WeeklyStats(Base):
“”“Недельная статистика — кеш для отчёта.”””
**tablename** = “weekly_stats”

```
id              = Column(Integer, primary_key=True)
user_id         = Column(Integer, nullable=False)
week_start      = Column(String(10), nullable=False)   # "YYYY-MM-DD" понедельник
days_done       = Column(Integer, default=0)
days_failed     = Column(Integer, default=0)
xp_earned       = Column(Integer, default=0)
xp_lost         = Column(Integer, default=0)
materials_read  = Column(Integer, default=0)
max_streak      = Column(Integer, default=0)
created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

# ─────────────────────────────────────────────

# ИНИЦИАЛИЗАЦИЯ БД

# ─────────────────────────────────────────────

def init_db():
Base.metadata.create_all(engine)

def get_session():
return Session()

def get_or_create_user(session, telegram_id: int, username: str = None, first_name: str = None) -> User:
user = session.query(User).filter_by(telegram_id=telegram_id).first()
if not user:
user = User(
telegram_id=telegram_id,
username=username,
first_name=first_name or “Монарх”
)
session.add(user)
session.commit()
return user

def get_today_report(session, user_id: int, today: str) -> DailyReport | None:
return session.query(DailyReport).filter_by(
user_id=user_id, date=today
).first()

def create_today_report(session, user_id: int, today: str, message_id: int = None) -> DailyReport:
report = DailyReport(user_id=user_id, date=today, message_id=message_id)
session.add(report)
session.commit()
return report
