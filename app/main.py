import schedule
import time
import logging

from app.api_client import fetch_rates
from app.db import save_request, save_responses
from app.config import settings

# Логгер для консоли
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Логгер ошибок в файл
file_handler = logging.FileHandler("errors.log")
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(file_handler)


def job():
    """Основная задача: запрос API → сохранение в БД."""
    logger.info("Запуск задачи — запрос курсов валют...")

    try:
        result = fetch_rates()

        request_id = save_request(
            base_currency=result["base"],
            endpoint=result["endpoint"],
            status_code=result["status_code"]
        )
        logger.info(f"Запрос сохранён, request_id={request_id}")

        if result["rates"]:
            save_responses(request_id, result["rates"])
            logger.info(f"Сохранено {len(result['rates'])} курсов: {list(result['rates'].keys())}")
        else:
            logger.warning("API вернул пустой список курсов")

    except Exception as e:
        logger.error(f"Ошибка при выполнении задачи: {e}")


def main():
    logger.info(f"Сервис запущен. Интервал: каждые {settings.FETCH_INTERVAL} мин.")

    job()

    schedule.every(settings.FETCH_INTERVAL).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()