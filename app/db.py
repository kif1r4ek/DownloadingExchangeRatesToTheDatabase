import psycopg2
from app.config import settings


def get_connection():
    try:
        return psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            connect_timeout=5,
        )
    except psycopg2.OperationalError as e:
        raise ConnectionError(
            f"Не удалось подключиться к PostgreSQL ({settings.DB_HOST}:{settings.DB_PORT}, db={settings.DB_NAME}, user={settings.DB_USER}). "
            "Проверьте, что сервер БД запущен и принимает TCP-подключения."
        ) from e


def init_db():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS public.requests (
                id SERIAL PRIMARY KEY,
                base_currency TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                status_code INT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS public.responses (
                id SERIAL PRIMARY KEY,
                request_id INT NOT NULL REFERENCES public.requests(id),
                currency_code TEXT NOT NULL,
                rate NUMERIC(18, 6) NOT NULL
            );
            """
        )
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()


def save_request(base_currency: str, endpoint: str, status_code: int) -> int:
    """
    Сохраняет запрос в таблицу requests.
    Возвращает id созданной строки.
    """
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO public.requests (base_currency, endpoint, status_code)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (base_currency, endpoint, status_code)
        )
        request_id = cursor.fetchone()[0]
        connection.commit()
        return request_id
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()


def save_responses(request_id: int, rates: dict):
    """
    Сохраняет курсы валют в таблицу responses.
    rates — словарь вида {"EUR": 0.92, "GBP": 0.79, "UAH": 41.5}
    """
    connection = get_connection()
    cursor = connection.cursor()

    try:
        for currency_code, rate in rates.items():
            cursor.execute(
                """
                INSERT INTO public.responses (request_id, currency_code, rate)
                VALUES (%s, %s, %s)
                """,
                (request_id, currency_code, rate)
            )
        connection.commit()

    except Exception as e:
        connection.rollback()
        raise e

    finally:
        cursor.close()
        connection.close()
