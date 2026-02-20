import requests
from app.config import settings


def fetch_rates(base_currency: str = "USD", targets: str = "EUR,GBP,UAH") -> dict:
    """
    Запрашивает курсы валют у FastForex API.
    Возвращает словарь:
    {
        "status_code": 200,
        "base": "USD",
        "endpoint": "/fetch-multi",
        "rates": {"EUR": 0.92, "GBP": 0.79, "UAH": 41.5}
    }
    """
    endpoint = "/fetch-multi"
    url = f"{settings.API_URL}{endpoint}"

    params = {
        "from": base_currency,
        "to": targets,
        "api_key": settings.API_KEY
    }

    response = requests.get(url, params=params, timeout=10)

    data = response.json()

    return {
        "status_code": response.status_code,
        "base": base_currency,
        "endpoint": endpoint,
        "rates": data.get("results", {})
    }

