from __future__ import annotations

from dataclasses import dataclass
from typing import List


HIGH_RISK_BRANDS = {
    "apple",
    "dyson",
    "jbl",
    "samsung",
    "xiaomi",
    "nike",
    "adidas",
}

TRIGGER_WORDS = {
    "копия",
    "реплика",
    "1:1",
    "не оригинал",
    "аналог",
    "аналогичный",
}


@dataclass
class ProductInput:
    marketplace: str
    title: str
    brand: str
    price: float
    median_market_price: float
    rating: float
    reviews_count: int
    seller_name: str
    seller_official: bool
    seller_age_days: int
    description: str


@dataclass
class RiskResult:
    score: int
    level: str
    reasons: List[str]


def _risk_level(score: int) -> str:
    if score >= 75:
        return "очень высокий"
    if score >= 50:
        return "высокий"
    if score >= 25:
        return "средний"
    return "низкий"


def evaluate_counterfeit_risk(product: ProductInput) -> RiskResult:
    reasons: List[str] = []
    score = 5

    if product.median_market_price > 0:
        ratio = product.price / product.median_market_price
        if ratio <= 0.55:
            score += 35
            reasons.append("Цена более чем на 45% ниже рыночной.")
        elif ratio <= 0.75:
            score += 20
            reasons.append("Цена заметно ниже рыночной (на 25%+).")

    if product.rating < 4.2:
        score += 15
        reasons.append("Низкий рейтинг товара/карточки.")
    elif product.rating < 4.5:
        score += 7
        reasons.append("Рейтинг немного ниже желательного для оригинального товара.")

    if product.reviews_count < 20:
        score += 12
        reasons.append("Слишком мало отзывов для уверенной проверки.")
    elif product.reviews_count < 80:
        score += 6
        reasons.append("Отзывов пока немного.")

    if product.seller_age_days < 30:
        score += 18
        reasons.append("Продавец очень новый (до 30 дней).")
    elif product.seller_age_days < 120:
        score += 8
        reasons.append("Продавец сравнительно новый (до 120 дней).")

    brand_lower = product.brand.strip().lower()
    if brand_lower in HIGH_RISK_BRANDS and not product.seller_official:
        score += 16
        reasons.append("Бренд из зоны повышенного риска, продавец не отмечен как официальный.")

    text = f"{product.title} {product.description}".lower()
    hit_words = [w for w in TRIGGER_WORDS if w in text]
    if hit_words:
        score += 25
        reasons.append(f"В описании есть маркеры возможной реплики: {', '.join(hit_words)}.")

    marketplace = product.marketplace.strip().lower()
    if marketplace not in {"kaspi", "wb", "wildberries", "ozon"}:
        score += 6
        reasons.append("Маркетплейс не из поддерживаемого списка, данные менее предсказуемы.")

    score = max(0, min(100, score))
    level = _risk_level(score)
    if not reasons:
        reasons.append("Явных красных флагов не обнаружено по заданным данным.")

    return RiskResult(score=score, level=level, reasons=reasons)
