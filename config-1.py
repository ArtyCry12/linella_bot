"""
Конфигурация бота.
Токены читаются из файла .env (безопасно) или из переменных окружения.

Создайте файл .env в папке бота:
    TELEGRAM_BOT_TOKEN=7123456789:AAF...
    ANTHROPIC_API_KEY=sk-ant-...
"""

import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env файла

# ─── Обязательные настройки ─────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError(
        "❌ Не задан TELEGRAM_BOT_TOKEN!\n"
        "Создайте файл .env и добавьте: TELEGRAM_BOT_TOKEN=ваш_токен"
    )

if not OPENAI_API_KEY:
    raise ValueError(
        "❌ Не задан OPENAI_API_KEY!\n"
        "Создайте файл .env и добавьте: OPENAI_API_KEY=ваш_ключ"
    )

# ─── Дополнительные настройки ────────────────────────────────────────────────

# Максимальное количество сообщений в истории диалога на одного пользователя
# (старые сообщения обрезаются, чтобы не превышать лимит токенов)
MAX_HISTORY_MESSAGES: int = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
