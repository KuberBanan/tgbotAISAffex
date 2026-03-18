from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


SUSPICIOUS_KEYWORDS = {
    "реплика": 35,
    "копия": 30,
    "аналог": 20,
    "aaa": 30,
    "1:1": 25,
    "лухари": 15,
    "без коробки": 10,
    "не оригинал": 45,
}

SAFE_KEYWORDS = {
    "оригинал": -10,
    "официальный": -15,
    "сертификат": -10,
    "гарантия": -8,
}


@dataclass
class RiskSignal:
    label: str
    score_delta: int


@dataclass
class RiskResult:
    score: int
    level: str
    reasons: list[str]
    recommendations: list[str]



def _normalize_text(text: str) -> str:
    return " ".join(text.lower().split())



def extract_keyword_signals(text: str) -> list[RiskSignal]:
    normalized = _normalize_text(text)
    signals: list[RiskSignal] = []

    for keyword, points in SUSPICIOUS_KEYWORDS.items():
        if keyword in normalized:
            signals.append(RiskSignal(f"Найден подозрительный маркер: '{keyword}'", points))

    for keyword, points in SAFE_KEYWORDS.items():
        if keyword in normalized:
            signals.append(RiskSignal(f"Найден маркер доверия: '{keyword}'", points))

    return signals



def extract_price_signals(current_price: float | None, reference_price: float | None) -> list[RiskSignal]:
    if current_price is None or reference_price is None or reference_price <= 0:
        return []

    discount = (reference_price - current_price) / reference_price
    signals: list[RiskSignal] = []

    if discount >= 0.6:
        signals.append(RiskSignal("Цена ниже референса более чем на 60%", 40))
    elif discount >= 0.45:
        signals.append(RiskSignal("Цена ниже референса более чем на 45%", 28))
    elif discount >= 0.3:
        signals.append(RiskSignal("Цена ниже референса более чем на 30%", 18))
    elif discount <= -0.3:
        signals.append(RiskSignal("Цена выше референса на 30%+ (редкий товар/наценка)", 3))

    return signals



def aggregate_signals(signals: Iterable[RiskSignal]) -> RiskResult:
    reasons: list[str] = []
    score = 0

    for signal in signals:
        score += signal.score_delta
        reasons.append(f"{signal.label} ({signal.score_delta:+d})")

    score = max(0, min(100, score))

    if score >= 65:
        level = "Высокий риск"
        recommendations = [
            "Запросите серийный номер и чек.",
            "Сверьте продавца с официальным списком бренда.",
            "Избегайте полной предоплаты до проверки товара.",
        ]
    elif score >= 35:
        level = "Средний риск"
        recommendations = [
            "Попросите дополнительные фото упаковки и маркировки.",
            "Проверьте отзывы именно на этого продавца.",
            "Сравните цену с 2-3 другими площадками.",
        ]
    else:
        level = "Низкий риск"
        recommendations = [
            "Риск низкий, но всё равно проверьте рейтинг продавца.",
            "Сохраняйте скриншоты карточки и условий покупки.",
        ]

    return RiskResult(score=score, level=level, reasons=reasons, recommendations=recommendations)
