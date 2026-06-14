# Telegram Relay

VPS за пределами РФ, который собирает публичные Telegram-каналы и отправляет посты на основной сервер.

## Требования

- VPS любой (€5/мес. достаточно): Hetzner EU, DigitalOcean, Vultr
- Python 3.10+
- Аккаунт Telegram (обычный номер телефона)
- API-ключи с my.telegram.org

## Настройка

### 1. Получить API-ключи Telegram

Открыть https://my.telegram.org → "API development tools" → создать приложение.
Сохранить `api_id` и `api_hash`.

### 2. Установить зависимости

```bash
pip install telethon httpx
```

### 3. Создать файл .env

```bash
TG_API_ID=1234567
TG_API_HASH=abcdef1234567890abcdef1234567890
INGEST_URL=https://your-main-server.ru/api/tg-ingest
INGEST_TOKEN=сюда-случайный-токен-32-символа
INTERVAL_MINUTES=30
```

### 4. Прописать тот же токен на основном сервере

В `data/secrets.json` основного приложения:

```json
"TG_RELAY_TOKEN": "сюда-тот-же-токен"
```

### 5. Авторизоваться в Telegram (один раз)

```bash
source .env && python tg_relay.py --auth
```

Введёт номер телефона и код из SMS/приложения. Создаст файл `tg_session.session`.

### 6. Запустить

С конфигом основного приложения (читает каналы из config.json):

```bash
source .env && python tg_relay.py --config /path/to/config.json
```

Или с явным списком каналов:

```bash
source .env && python tg_relay.py --channels rian_ru tass_agency rbc_news filimonov_35
```

### 7. Запуск как systemd-сервис

```ini
[Unit]
Description=Telegram Relay for Mention Monitor

[Service]
WorkingDirectory=/opt/tg_relay
EnvironmentFile=/opt/tg_relay/.env
ExecStart=/usr/bin/python3 tg_relay.py --config /opt/tg_relay/config.json
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now tg-relay
```

## Что собирается

Все публичные каналы из `config.json`, у которых в URL есть `/telegram/channel/`.
Список из 27 каналов уже прописан (РИА, ТАСС, РБК, Коммерсантъ, региональные и тематические).

## Как работает матчинг проектов

Каждый входящий пост проверяется на наличие ключевых слов из `config.json → projects[].queries`.
Если текст содержит ключевое слово — пост относится к соответствующему проекту мониторинга.
Если совпадений нет — пост уходит в первый проект по умолчанию.
