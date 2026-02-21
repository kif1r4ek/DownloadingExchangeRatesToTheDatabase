# Загрузка курсов валют в базу данных

Сервис автоматически запрашивает курсы валют через [FastForex API](https://fastforex.readme.io/reference/introduction) каждые N минут и сохраняет результаты в PostgreSQL.

## Стек

- Python 3.12
- PostgreSQL 16
- Docker & Docker Compose
- Библиотеки: `requests`, `psycopg2-binary`, `schedule`, `pydantic-settings`

## Структура проекта

```
├── app/
│   ├── __init__.py      # Маркер пакета
│   ├── main.py          # Точка входа, планировщик
│   ├── api_client.py    # Запросы к FastForex API
│   ├── db.py            # Работа с PostgreSQL
│   └── config.py        # Конфигурация из .env
├── sql/
│   └── init.sql         # Создание таблиц
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Как развернуть через Docker Compose

1. Клонировать репозиторий:

```bash
git clone https://github.com/kif1r4ek/DownloadingExchangeRatesToTheDatabase.git
cd DownloadingExchangeRatesToTheDatabase
```

2. Создать `.env` файл из шаблона и вписать свой API-ключ:

```bash
cp .env.example .env
# Открыть .env и вставить API_KEY от fastforex.io
```

3. Запустить через Docker Compose:

```bash
docker-compose up --build
```

Сервис поднимет PostgreSQL, создаст таблицы и начнёт опрашивать API каждые N минут (по умолчанию 5).

## Пример `.env`

```env
API_KEY=your_fastforex_api_key_here
API_URL=https://api.fastforex.io
TARGET_CURRENCIES=EUR,GBP,UAH

# Для docker-compose — DB_HOST=db; для локального запуска — DB_HOST=localhost
DB_HOST=db
DB_PORT=5432
DB_NAME=forex
DB_USER=postgres
DB_PASSWORD=postgres

FETCH_INTERVAL=5
```

## Схема базы данных

### Таблица `requests`

| Колонка       | Тип       | Описание                        |
|---------------|-----------|---------------------------------|
| id            | SERIAL PK | Уникальный идентификатор        |
| base_currency | TEXT      | Базовая валюта (например "USD") |
| endpoint      | TEXT      | Эндпоинт API                    |
| status_code   | INT       | HTTP-код ответа                 |
| created_at    | TIMESTAMP | Время запроса                   |

### Таблица `responses`

| Колонка       | Тип           | Описание                         |
|---------------|---------------|----------------------------------|
| id            | SERIAL PK     | Уникальный идентификатор         |
| request_id    | INT (FK)      | Ссылка на requests.id            |
| currency_code | TEXT          | Код валюты (например "EUR")      |
| rate          | NUMERIC(18,6) | Курс относительно базовой валюты |

## SQL-запрос с JOIN

Выгружает историю запросов вместе с полученными курсами:

```sql
SELECT
    r.id          AS request_id,
    r.base_currency,
    r.endpoint,
    r.status_code,
    r.created_at,
    resp.currency_code,
    resp.rate
FROM requests r
JOIN responses resp ON r.id = resp.request_id
ORDER BY r.created_at DESC, resp.currency_code;
```

## Логирование

| Поток          | Уровень      | Назначение                                |
|----------------|--------------|-------------------------------------------|
| Консоль        | INFO и выше  | Штатный ход работы                        |
| `errors.log`   | ERROR и выше | Ошибки подключения к API и БД, таймауты   |

Файл `errors.log` создаётся рядом с точкой входа (в Docker — `/app/errors.log`).

Пример записи при таймауте API:
```
2025-01-01 12:00:00,000 [ERROR] [app.main] Таймаут при запросе к API: Таймаут запроса к API (10 с): https://api.fastforex.io/fetch-multi
```

Пример записи при недоступности БД:
```
2025-01-01 12:00:00,000 [ERROR] [app.main] Ошибка подключения к БД при инициализации: Не удалось подключиться к PostgreSQL (db:5432, db=forex, user=postgres). Проверьте, что сервер БД запущен и принимает TCP-подключения.
```
