"""A small Telegram bot that stores and shares cat photos.

Run it with:
    TELEGRAM_BOT_TOKEN=123:abc python bot.py
"""

import logging
import os
import random
import uuid
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

CAT_NAME = os.getenv("CAT_NAME", "мой кот")
PHOTO_DIR = Path(os.getenv("CAT_PHOTO_DIR", "cat_photos"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a friendly greeting and short help text."""
    del context
    await update.message.reply_text(
        f"Привет! Я фотоальбом для кота: {CAT_NAME} 🐾\n\n"
        "Отправь мне фото кота, и я сохраню его локально.\n\n"
        "Команды:\n"
        "/start — показать это сообщение\n"
        "/help — помощь\n"
        "/about — информация об альбоме\n"
        "/count — сколько фоток сохранено\n"
        "/random_cat — прислать случайную фотку"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a compact help message."""
    del context
    await update.message.reply_text(
        "Как пользоваться:\n"
        "1. Просто отправь сюда фото кота.\n"
        "2. Бот сохранит файл в папку cat_photos/.\n"
        "3. Напиши /random_cat, чтобы получить случайное фото.\n"
        "4. Напиши /count, чтобы узнать размер коллекции."
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tell users what this bot stores."""
    del context
    await update.message.reply_text(
        f"Это личный Telegram-альбом для фоток кота: {CAT_NAME}.\n"
        f"Папка хранения на сервере: {PHOTO_DIR.resolve()}"
    )


async def count_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show how many photos are stored locally."""
    del context
    total = len(list_saved_photos())
    await update.message.reply_text(f"Сохранено фоток: {total}")


async def save_cat_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download the largest photo variant from a Telegram message."""
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)

    photo = update.message.photo[-1]
    telegram_file = await context.bot.get_file(photo.file_id)
    file_name = f"{update.effective_user.id}_{uuid.uuid4().hex}.jpg"
    destination = PHOTO_DIR / file_name

    await telegram_file.download_to_drive(custom_path=destination)
    await update.message.reply_text(
        f"Готово, сохранил фото для альбома {CAT_NAME} 🐱\n"
        f"Файл: {destination.name}"
    )


async def send_random_cat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a random saved cat photo back to the chat."""
    del context
    photos = list_saved_photos()
    if not photos:
        await update.message.reply_text(
            "Пока нет сохранённых фоток. Отправь мне первое фото кота!"
        )
        return

    photo_path = random.choice(photos)
    with photo_path.open("rb") as photo_file:
        await update.message.reply_photo(
            photo=photo_file,
            caption=f"Случайная фотка из альбома {CAT_NAME} 🐾",
        )


def list_saved_photos() -> list[Path]:
    """Return saved JPG photos sorted by file name."""
    if not PHOTO_DIR.exists():
        return []
    return sorted(PHOTO_DIR.glob("*.jpg"))


def main() -> None:
    """Start the bot using long polling."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "Set TELEGRAM_BOT_TOKEN first. Example: "
            "TELEGRAM_BOT_TOKEN=123:abc python bot.py"
        )

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("count", count_photos))
    application.add_handler(CommandHandler("random_cat", send_random_cat))
    application.add_handler(MessageHandler(filters.PHOTO, save_cat_photo))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
