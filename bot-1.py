"""
╔══════════════════════════════════════════════════════════╗
║         LINELLA AI — Telegram Bot (aiogram 3.x)          ║
║         Работает через Anthropic Claude API              ║
╚══════════════════════════════════════════════════════════╝

Зависимости (установить перед запуском):
    pip install aiogram anthropic python-dotenv

Запуск:
    python bot.py
"""

import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.client.default import DefaultBotProperties
from openai import OpenAI

from config import TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, MAX_HISTORY_MESSAGES
from system_prompt import SYSTEM_PROMPT

# ─── Логирование ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Инициализация ───────────────────────────────────────────────────────────
bot = Bot(
    token=TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()

# Клиент OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# История диалогов: { user_id: [ {role, content}, ... ] }
conversation_history: dict[int, list[dict]] = {}


# ════════════════════════════════════════════════════════════════════════════
#  КЛАВИАТУРЫ
# ════════════════════════════════════════════════════════════════════════════

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню с четырьмя кнопками."""
    buttons = [
        [
            InlineKeyboardButton(text="🛒 Каталог товаров", callback_data="menu_catalog"),
            InlineKeyboardButton(text="🏷️ Акции",           callback_data="menu_sales"),
        ],
        [
            InlineKeyboardButton(text="💳 Моя карта лояльности", callback_data="menu_loyalty"),
            InlineKeyboardButton(text="🆘 Поддержка",            callback_data="menu_support"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка «← Главное меню»."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="← Главное меню", callback_data="menu_main")]
        ]
    )


# ════════════════════════════════════════════════════════════════════════════
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ════════════════════════════════════════════════════════════════════════════

def get_history(user_id: int) -> list[dict]:
    """Возвращает историю диалога пользователя."""
    return conversation_history.get(user_id, [])


def add_to_history(user_id: int, role: str, content: str) -> None:
    """Добавляет сообщение в историю, обрезая старые при необходимости."""
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    conversation_history[user_id].append({"role": role, "content": content})
    # Оставляем только последние N сообщений (не считая system prompt)
    if len(conversation_history[user_id]) > MAX_HISTORY_MESSAGES:
        conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY_MESSAGES:]


def clear_history(user_id: int) -> None:
    """Сбрасывает историю диалога."""
    conversation_history.pop(user_id, None)


async def ask_claude(user_id: int, user_message: str) -> str:
    """
    Отправляет запрос в Claude API с сохранением контекста диалога.
    Возвращает текстовый ответ ассистента.
    """
    add_to_history(user_id, "user", user_message)
    history = get_history(user_id)

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(user_id)

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1024,
            messages=messages,
        )
        assistant_reply = response.choices[0].message.content
        add_to_history(user_id, "assistant", assistant_reply)
        return assistant_reply

    except Exception as e:
        logger.error("OpenAI API error: %s", e)
        return (
            "⚠️ Извините, произошла техническая ошибка. "
            "Пожалуйста, попробуйте позже или свяжитесь с поддержкой: "
            "<b>📞 0-800-12345</b>"
        )


# ════════════════════════════════════════════════════════════════════════════
#  HANDLERS — КОМАНДЫ
# ════════════════════════════════════════════════════════════════════════════

@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Приветствие при /start."""
    clear_history(message.from_user.id)
    name = message.from_user.first_name or "друг"
    await message.answer(
        f"👋 Привет, <b>{name}</b>!\n\n"
        "Я — <b>Linella AI</b>, ваш персональный помощник "
        "крупнейшей сети супермаркетов Молдовы 🛒\n\n"
        "Помогу найти товары, расскажу об акциях, программе лояльности "
        "и отвечу на любые вопросы.\n\n"
        "Выберите раздел ниже или просто напишите свой вопрос:",
        reply_markup=main_menu_keyboard(),
    )


@dp.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    """Показывает главное меню по команде /menu."""
    await message.answer(
        "📋 <b>Главное меню Linella</b>\n\nВыберите нужный раздел:",
        reply_markup=main_menu_keyboard(),
    )


@dp.message(Command("reset"))
async def cmd_reset(message: Message) -> None:
    """Сбрасывает историю диалога."""
    clear_history(message.from_user.id)
    await message.answer(
        "🔄 История диалога очищена. Начинаем сначала!\n\n"
        "Чем могу помочь?",
        reply_markup=main_menu_keyboard(),
    )


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Справка по командам."""
    await message.answer(
        "ℹ️ <b>Доступные команды:</b>\n\n"
        "/start — начать диалог заново\n"
        "/menu  — открыть главное меню\n"
        "/reset — очистить историю диалога\n"
        "/help  — эта справка\n\n"
        "Или просто напишите любой вопрос — я отвечу! 😊",
        reply_markup=main_menu_keyboard(),
    )


# ════════════════════════════════════════════════════════════════════════════
#  HANDLERS — CALLBACK (кнопки меню)
# ════════════════════════════════════════════════════════════════════════════

@dp.callback_query(F.data == "menu_main")
async def cb_main_menu(callback: CallbackQuery) -> None:
    """Возврат в главное меню."""
    await callback.message.edit_text(
        "📋 <b>Главное меню Linella</b>\n\nВыберите нужный раздел:",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "menu_catalog")
async def cb_catalog(callback: CallbackQuery) -> None:
    """Раздел: Каталог товаров."""
    user_id = callback.from_user.id
    thinking_msg = await callback.message.answer("🔍 Загружаю информацию о каталоге…")

    reply = await ask_claude(
        user_id,
        "Расскажи мне о каталоге товаров в Linella. "
        "Какие основные категории есть? Как найти местные молдавские продукты (Produs Local)?",
    )
    await thinking_msg.delete()
    await callback.message.answer(reply, reply_markup=back_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "menu_sales")
async def cb_sales(callback: CallbackQuery) -> None:
    """Раздел: Акции."""
    user_id = callback.from_user.id
    thinking_msg = await callback.message.answer("🏷️ Загружаю информацию об акциях…")

    reply = await ask_claude(
        user_id,
        "Расскажи об актуальных акциях и скидках в Linella. "
        "Где можно найти акционную газету и как узнать о скидках «Лучшая цена»?",
    )
    await thinking_msg.delete()
    await callback.message.answer(reply, reply_markup=back_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "menu_loyalty")
async def cb_loyalty(callback: CallbackQuery) -> None:
    """Раздел: Программа лояльности."""
    user_id = callback.from_user.id
    thinking_msg = await callback.message.answer("💳 Загружаю информацию о карте лояльности…")

    reply = await ask_claude(
        user_id,
        "Расскажи подробно о программе лояльности Linella Card: "
        "как накапливаются баллы, как установить мобильное приложение, "
        "как добавить карту в Google Wallet, и какие персонализированные купоны доступны?",
    )
    await thinking_msg.delete()
    await callback.message.answer(reply, reply_markup=back_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "menu_support")
async def cb_support(callback: CallbackQuery) -> None:
    """Раздел: Поддержка."""
    await callback.message.answer(
        "🆘 <b>Служба поддержки Linella</b>\n\n"
        "📞 <b>Телефон:</b> 0-800-LINELLA (бесплатно)\n"
        "📧 <b>Email:</b> support@linella.md\n"
        "🌐 <b>Сайт:</b> <a href='https://linella.md/ro'>linella.md</a>\n"
        "📍 <b>Карта магазинов:</b> доступна на сайте\n\n"
        "💬 Или задайте вопрос прямо здесь — я постараюсь помочь!",
        reply_markup=back_keyboard(),
        disable_web_page_preview=True,
    )
    await callback.answer()


# ════════════════════════════════════════════════════════════════════════════
#  HANDLER — СВОБОДНЫЙ ТЕКСТ (основной чат с ИИ)
# ════════════════════════════════════════════════════════════════════════════

@dp.message(F.text)
async def handle_message(message: Message) -> None:
    """
    Обрабатывает любое текстовое сообщение пользователя.
    Отправляет его в Claude и возвращает ответ.
    """
    user_id = message.from_user.id
    user_text = message.text.strip()

    if not user_text:
        return

    # Показываем индикатор «печатает»
    await bot.send_chat_action(message.chat.id, action="typing")
    thinking_msg = await message.answer("💭 Обрабатываю ваш запрос…")

    reply = await ask_claude(user_id, user_text)

    await thinking_msg.delete()
    await message.answer(reply, reply_markup=back_keyboard())


# ════════════════════════════════════════════════════════════════════════════
#  ЗАПУСК БОТА
# ════════════════════════════════════════════════════════════════════════════

async def main() -> None:
    logger.info("🟢 Linella AI Bot запущен!")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
