from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


@dataclass
class ProductData:
    platform: str
    title: str
    current_price: float | None
    url: str
    raw_text: str



def detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "kaspi" in host:
        return "Kaspi"
    if "wildberries" in host or host.endswith("wb.ru"):
        return "Wildberries"
    if "ozon" in host:
        return "Ozon"
    return "Unknown"



def _extract_price_from_text(text: str) -> float | None:
    patterns = [
        r"(\d[\d\s]{2,})\s*(?:₸|тг|тенге)",
        r"(\d[\d\s]{2,})\s*(?:₽|руб)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            digits = re.sub(r"\D", "", match.group(1))
            if digits:
                return float(digits)
    return None



def fetch_product(url: str, timeout_seconds: int = 10) -> ProductData:
    platform = detect_platform(url)
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=timeout_seconds)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title = (soup.title.text if soup.title else "").strip()

    raw_text = " ".join(soup.stripped_strings)
    current_price = _extract_price_from_text(raw_text)

    return ProductData(
        platform=platform,
        title=title or "Без названия",
        current_price=current_price,
        url=url,
        raw_text=raw_text,
    )
