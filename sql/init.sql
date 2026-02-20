CREATE TABLE IF NOT EXISTS requests (
    id SERIAL PRIMARY KEY,
    base_currency TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    status_code INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS responses (
    id SERIAL PRIMARY KEY,
    request_id INT NOT NULL REFERENCES requests(id),
    currency_code TEXT NOT NULL,
    rate NUMERIC(18, 6) NOT NULL
);

