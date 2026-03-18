from __future__ import annotations

import logging
import os
import re

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from marketplace_scraper import fetch_product
from risk_engine import aggregate_signals, extract_keyword_signals, extract_price_signals


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


HELP_TEXT = (
    "Я анализирую карточки товаров с Kaspi / Wildberries / Ozon и оцениваю риск подделки.\n\n"
    "Команда:\n"
    "/check <url> [референсная_цена]\n\n"
    "Примеры:\n"
    "/check https://kaspi.kz/shop/p/xxxx 220000\n"
    "/check https://www.ozon.ru/product/xxxxx\n\n"
    "Референсная цена — официальная цена (если знаете)."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Отправь /help чтобы увидеть формат проверки товара."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)



def _parse_check_args(args: list[str]) -> tuple[str, float | None]:
    if not args:
        raise ValueError("Нужна ссылка на товар.")

    url = args[0]
    if not re.match(r"https?://", url):
        raise ValueError("Ссылка должна начинаться с http:// или https://")

    reference_price = None
    if len(args) > 1:
        try:
            reference_price = float(args[1].replace("_", "").replace(",", "."))
        except ValueError as exc:
            raise ValueError("Референсная цена должна быть числом.") from exc

    return url, reference_price


async def check_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        url, reference_price = _parse_check_args(context.args)
    except ValueError as error:
        await update.message.reply_text(f"Ошибка: {error}\n\n{HELP_TEXT}")
        return

    await update.message.reply_text("Проверяю карточку товара, подождите...")

    timeout_seconds = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))

    try:
        product = fetch_product(url, timeout_seconds=timeout_seconds)
    except Exception as error:  # noqa: BLE001
        logger.exception("Ошибка загрузки карточки товара")
        await update.message.reply_text(
            f"Не удалось загрузить страницу: {error}\n"
            "Проверьте ссылку и попробуйте ещё раз."
        )
        return

    keyword_signals = extract_keyword_signals(product.title + " " + product.raw_text)
    price_signals = extract_price_signals(product.current_price, reference_price)
    result = aggregate_signals([*keyword_signals, *price_signals])

    reasons = "\n".join(f"• {item}" for item in result.reasons) or "• Явные маркеры не найдены"
    recommendations = "\n".join(f"• {item}" for item in result.recommendations)

    price_text = (
        f"{product.current_price:,.0f}".replace(",", " ")
        if product.current_price is not None
        else "не удалось определить"
    )

    answer = (
        f"Платформа: {product.platform}\n"
        f"Товар: {product.title}\n"
        f"Цена на карточке: {price_text}\n"
        f"Оценка риска: {result.level} ({result.score}/100)\n\n"
        f"Причины:\n{reasons}\n\n"
        f"Что сделать дальше:\n{recommendations}\n\n"
        "⚠️ Это эвристическая оценка, а не юридическая экспертиза."
    )

    await update.message.reply_text(answer)



def main() -> None:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError("Не найден TELEGRAM_BOT_TOKEN в переменных окружения.")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("check", check_product))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
