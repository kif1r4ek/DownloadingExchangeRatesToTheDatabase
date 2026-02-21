import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout

from app.config import settings


def fetch_rates(base_currency: str = "USD") -> dict:
    """
    Запрашивает курсы валют у FastForex API.
    Возвращает словарь:
    {
        "status_code": 200,
        "base": "USD",
        "endpoint": "/fetch-multi",
        "rates": {"EUR": 0.92, "GBP": 0.79, "UAH": 41.5}
    }
    Raises:
        TimeoutError: если сервер не ответил за 10 секунд.
        ConnectionError: если не удалось установить соединение с API.
    """
    endpoint = "/fetch-multi"
    url = f"{settings.API_URL}{endpoint}"

    params = {
        "from": base_currency,
        "to": settings.TARGET_CURRENCIES,
        "api_key": settings.API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except Timeout:
        raise TimeoutError(f"Таймаут запроса к API (10 с): {url}")
    except RequestsConnectionError as e:
        raise ConnectionError(f"Ошибка соединения с API ({url}): {e}")

    data = response.json()

    return {
        "status_code": response.status_code,
        "base": base_currency,
        "endpoint": endpoint,
        "rates": data.get("results", {}),
    }
