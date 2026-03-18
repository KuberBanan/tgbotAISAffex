from risk_engine import ProductInput, evaluate_counterfeit_risk


def test_high_risk_product():
    product = ProductInput(
        marketplace="ozon",
        title="Apple AirPods Pro 2",
        brand="Apple",
        price=9990,
        median_market_price=24990,
        rating=4.1,
        reviews_count=9,
        seller_name="Cheap Air",
        seller_official=False,
        seller_age_days=7,
        description="реплика 1:1, не оригинал",
    )

    result = evaluate_counterfeit_risk(product)

    assert result.score >= 75
    assert result.level == "очень высокий"


def test_low_risk_product():
    product = ProductInput(
        marketplace="kaspi",
        title="Dyson V15",
        brand="Dyson",
        price=349990,
        median_market_price=359990,
        rating=4.9,
        reviews_count=430,
        seller_name="Dyson Official",
        seller_official=True,
        seller_age_days=1000,
        description="Гарантия и официальный поставщик",
    )

    result = evaluate_counterfeit_risk(product)

    assert result.score < 25
    assert result.level == "низкий"
