import logging
import time

import schedule

from app.api_client import fetch_rates
from app.config import settings
from app.db import init_db, save_request, save_responses

# --- Настройка логирования ---

# Консольный хендлер: INFO и выше
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

# Файловый хендлер: только ERROR и выше → errors.log
file_handler = logging.FileHandler("errors.log", encoding="utf-8")
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s")
)

# Корневой логгер — оба хендлера применяются ко всем модулям (app.db, app.api_client)
logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])

logger = logging.getLogger(__name__)


def job():
    """Основная задача: запрос API → сохранение в БД."""
    logger.info("Запуск задачи — запрос курсов валют...")

    # Шаг 1: запрос к API
    try:
        result = fetch_rates()
    except TimeoutError as e:
        logger.error(f"Таймаут при запросе к API: {e}")
        return
    except ConnectionError as e:
        logger.error(f"Ошибка соединения с API: {e}")
        return
    except Exception as e:
        logger.error(f"Неожиданная ошибка при запросе к API: {e}")
        return

    # Шаг 2: сохранение в БД
    try:
        request_id = save_request(
            base_currency=result["base"],
            endpoint=result["endpoint"],
            status_code=result["status_code"],
        )
        logger.info(f"Запрос сохранён, request_id={request_id}")

        if result["rates"]:
            save_responses(request_id, result["rates"])
            logger.info(
                f"Сохранено {len(result['rates'])} курсов: {list(result['rates'].keys())}"
            )
        else:
            logger.warning("API вернул пустой список курсов")

    except ConnectionError as e:
        logger.error(f"Ошибка подключения к БД: {e}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в БД: {e}")


def main():
    logger.info(f"Сервис запущен. Интервал: каждые {settings.FETCH_INTERVAL} мин.")

    try:
        init_db()
    except ConnectionError as e:
        logger.error(f"Ошибка подключения к БД при инициализации: {e}")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        raise SystemExit(1)

    job()

    schedule.every(settings.FETCH_INTERVAL).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
