# config.py — MONARCH BOT

# Все переменные окружения. Токены здесь не хранятся — только в Railway Variables.

import os
import sys

# ─────────────────────────────────────────────

# ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ

# При отсутствии — бот не запустится.

# ─────────────────────────────────────────────

BOT_TOKEN: str = os.getenv(“BOT_TOKEN”, “”)
if not BOT_TOKEN:
sys.exit(“ОШИБКА: BOT_TOKEN не задан. Добавь в Railway Variables.”)

_user_id = os.getenv(“USER_ID”, “”)
if not _user_id:
sys.exit(“ОШИБКА: USER_ID не задан. Добавь в Railway Variables.”)
USER_ID: int = int(_user_id)

_channel_id = os.getenv(“CHANNEL_ID”, “”)
if not _channel_id:
sys.exit(“ОШИБКА: CHANNEL_ID не задан. Добавь в Railway Variables.”)
CHANNEL_ID: int = int(_channel_id)

# ─────────────────────────────────────────────

# ОПЦИОНАЛЬНЫЕ

# ─────────────────────────────────────────────

# Часовой пояс (по умолчанию Киев)

TIMEZONE: str = os.getenv(“TIMEZONE”, “Europe/Kyiv”)

# Режим отладки

DEBUG: bool = os.getenv(“DEBUG”, “false”).lower() == “true”
