# 🛒 Бот отслеживания цен на маркетплейсах

Учебный проект — Telegram-бот, который следит за ценами и присылает:
- **еженедельный отчёт** об изменении цен в среднем;
- **мгновенное уведомление**, если цена изменилась сильнее порога.

## Запуск

```bash
pip install -r requirements.txt
cp .env.example .env   # заполните TELEGRAM_BOT_TOKEN
uvicorn app.main:app --reload
```

Бот запускается вместе с FastAPI и работает в фоне.

## Переменные окружения (.env)

| Переменная | Описание | По умолчанию |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота | — |
| `DATABASE_URL` | URL базы данных | `sqlite:///./db.sqlite3` |
| `PRICE_ALERT_THRESHOLD_PERCENT` | Порог для мгновенного алерта (%) | `10` |
| `PRICE_CHECK_INTERVAL_HOURS` | Интервал проверки цен (часы) | `6` |
| `WEEKLY_REPORT_DAY` | День еженедельного отчёта | `mon` |
| `WEEKLY_REPORT_HOUR` | Час отправки отчёта (UTC) | `10` |

## Команды бота

- `/start`, `/help` — справка
- Отправьте **ссылку** или **артикул** (`ozon:123`, `wb:123`, `yandex:123`, `aliexpress:123`) — добавить товар
- `/list` — список отслеживаемых товаров
- `/remove <id>` — удалить товар

## Поддерживаемые маркетплейсы

- Ozon (`ozon.ru`)
- Wildberries (`wildberries.ru`)
- Яндекс Маркет (`market.yandex.ru`)
- AliExpress (`aliexpress.ru`, `aliexpress.com`)
