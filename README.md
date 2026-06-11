# 📦 SHK Bot — Сканер и генератор штрих-кодов

Telegram-бот для сканирования и генерации штрих-кодов (Code128) и QR-кодов с OCR-fallback'ом.

## ✨ Возможности

- 📝 **Генерация штрих-кодов** — отправь текст → получи Code128
- 📷 **Сканирование с фото** — отправь фото → бот прочитает ШК/QR
- 🔤 **OCR fallback** — если штрих-код не найден, распознаёт текст
- 🛡️ **Rate limiting** — защита от спама (2с между запросами)
- 📦 **Ограничение размера** — максимум 20MB на файл
- 🔄 **Автоматическое переподключение** — работает 24/7

## 🚀 Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/Straiko/shk.git
cd shk

# 2. Виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 3. Зависимости
pip install -r requirements.txt

# 4. Конфигурация
cp .env.example .env
# Вписать BOT_TOKEN от @BotFather

# 5. Запуск
python main.py
```

## ⚙️ Конфигурация

Все настройки через `.env` файл (см. [.env.example](.env.example)):

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `BOT_TOKEN` | *обязательно* | Токен от @BotFather |
| `OCR_API_KEY` | `helloworld` | Ключ OCR.space (500 запросов/день) |
| `RATE_LIMIT_SECONDS` | `2` | Интервал между запросами (сек) |
| `MAX_FILE_SIZE_MB` | `20` | Макс. размер файла |
| `NUM_THREADS` | `4` | Кол-во потоков |

## 🏗️ Структура проекта

```
├── main.py              # Точка входа
├── config.py            # Конфигурация из .env
├── bot.py               # Фабрика бота
├── handlers/
│   ├── commands.py      # /start, /help, /version
│   ├── photo.py         # Обработка фото (ШК + OCR)
│   └── barcode.py       # Генерация Code128
├── services/
│   ├── scanner.py       # zxingcpp сканирование
│   └── ocr.py           # OCR.space API
├── utils/
│   ├── rate_limiter.py  # Rate limiting
│   └── file_manager.py  # Временные файлы
└── tests/               # 18 тестов (pytest)
```

## 🚀 Деплой

Подробная инструкция по деплою: [DEPLOY.md](DEPLOY.md)

## 🧪 Тесты

```bash
pytest tests/ -v
```

## 📋 Changelog

- **v3.0.0** — Рефакторинг: модульная архитектура, `.env` конфигурация, логирование, тесты
- **v2.0.0** — Многопоточность, rate limiting, автоочистка
- **v1.5.2** — Автоисправление ошибки OCR
- **v1.5.0** — Умный фильтр текста
- **v1.2.0** — Генерация баркода после фото
- **v1.1.0** — Чтение ШК/QR с фото
