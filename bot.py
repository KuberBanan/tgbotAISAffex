from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from risk_engine import ProductInput, evaluate_counterfeit_risk


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def _extract_json_payload(text: str) -> str:
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        raise ValueError("После /check нужно передать JSON с параметрами товара.")
    return parts[1].strip()


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    await update.message.reply_text(
        "Привет! Я бот для оценки риска подделки товаров на Kaspi/WB/Ozon.\n\n"
        "Отправь команду /check с JSON.\n"
        "Пример:\n"
        "/check {\"marketplace\":\"ozon\",\"title\":\"Apple AirPods Pro 2\","
        "\"brand\":\"Apple\",\"price\":12990,\"median_market_price\":24990,"
        "\"rating\":4.3,\"reviews_count\":17,\"seller_name\":\"Best Deals\","
        "\"seller_official\":false,\"seller_age_days\":8,"
        "\"description\":\"копия 1:1\"}"
    )


async def check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context

    try:
        payload = _extract_json_payload(update.message.text)
        raw = json.loads(payload)
        product = ProductInput(**raw)
    except ValueError as exc:
        await update.message.reply_text(f"Ошибка: {exc}")
        return
    except json.JSONDecodeError:
        await update.message.reply_text("Не удалось прочитать JSON. Проверьте формат.")
        return
    except TypeError as exc:
        await update.message.reply_text(f"Не хватает полей или неверные типы: {exc}")
        return

    result = evaluate_counterfeit_risk(product)

    reasons = "\n".join(f"• {r}" for r in result.reasons)
    response = (
        "Результат оценки:\n"
        f"Маркетплейс: {product.marketplace}\n"
        f"Товар: {product.title}\n"
        f"Оценка риска подделки: {result.score}/100 ({result.level})\n\n"
        "Почему:\n"
        f"{reasons}\n\n"
        "⚠️ Это не окончательное доказательство подделки, а аналитическая оценка по признакам."
    )

    logger.info("Risk evaluated: %s", asdict(result))
    await update.message.reply_text(response)


def main() -> None:
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не найден. Укажите его в .env")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("check", check_handler))

    logger.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
