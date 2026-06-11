<p align="center">
  <img src="https://img.shields.io/badge/version-3.0.2-blue?style=for-the-badge" alt="version">
  <img src="https://img.shields.io/badge/python-3.12+-green?style=for-the-badge&logo=python&logoColor=white" alt="python">
  <img src="https://img.shields.io/badge/license-MIT-orange?style=for-the-badge" alt="license">
  <img src="https://img.shields.io/badge/telegram-bot%20api-26458B?style=for-the-badge&logo=telegram&logoColor=white" alt="telegram">
</p>

<h1 align="center">SHK Bot</h1>

<p align="center">
  Telegram-бот для сканирования и генерации штрих-кодов<br>
  <sub>Code128 · QR-коды · OCR · Автодеплой</sub>
</p>

---

## Быстрый старт

```bash
git clone https://github.com/Straiko/shk.git && cd shk
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

---

## Платформы для деплоя

### VPS / Выделенный сервер

> Полный контроль, стабильность, 24/7 работа

#### Шаг 1 — Подготовка сервера

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y python3 python3-venv git

# Клонировать и установить
git clone https://github.com/Straiko/shk.git /opt/shk
cd /opt/shk
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

#### Шаг 2 — Конфигурация

```bash
cp .env.example .env
nano .env
```

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен от [@BotFather](https://t.me/BotFather) |
| `OCR_API_KEY` | Ключ [OCR.space](https://ocr.space/ocrapi/freekey) (или `helloworld`) |
| `ADMIN_USER_ID` | Ваш Telegram ID |
| `RATE_LIMIT_SECONDS` | Интервал между запросами (по умолчанию `2`) |
| `MAX_FILE_SIZE_MB` | Макс. размер файла (по умолчанию `20`) |

#### Шаг 3 — Автозапуск (systemd)

```bash
sudo tee /etc/systemd/system/shk-bot.service > /dev/null <<EOF
[Unit]
Description=SHK Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/shk
ExecStart=/opt/shk/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable shk-bot
sudo systemctl start shk-bot
```

#### Управление

| Команда | Действие |
|---------|----------|
| `sudo systemctl status shk-bot` | Статус |
| `sudo systemctl restart shk-bot` | Перезапуск |
| `sudo systemctl stop shk-bot` | Остановка |
| `sudo journalctl -u shk-bot -f` | Логи |

---

### Render

> Бесплатно, без сервера, автоматический деплой

1. Перейти на [render.com](https://render.com) → **New** → **Background Worker**
2. Подключить GitHub: `Straiko/shk`
3. Настроить:

| Параметр | Значение |
|----------|----------|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python main.py` |

4. Добавить **Environment Variables**:
   - `BOT_TOKEN` → ваш токен
   - `ADMIN_USER_ID` → ваш ID
5. **Deploy**

---

### Railway

> Быстрый старт, GitHub интеграция

```bash
npm install -g @railway/cli
railway login
railway init
railway variables set BOT_TOKEN=your_token
railway variables set ADMIN_USER_ID=your_id
railway up
```

---

### Docker

> Изолированная среда, переносимость

#### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

#### Запуск

```bash
docker build -t shk-bot .
docker run -d --name shk-bot --restart unless-stopped --env-file .env shk-bot
```

#### docker-compose.yml

```yaml
version: '3.8'
services:
  bot:
    build: .
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./data:/app/data
```

```bash
docker compose up -d
```

---

## Проверка

```bash
# Бот жив?
curl -s "https://api.telegram.org/botYOUR_TOKEN/getMe" | python3 -m json.tool

# Логи
tail -f bot.log
```

---

## Устранение проблем

| Проблема | Решение |
|----------|---------|
| Бот не отвечает | Проверьте `BOT_TOKEN` в `.env` |
| `ModuleNotFoundError` | Активируйте venv: `source venv/bin/activate` |
| Ошибка SQLite | Проверьте права на `data/bot.db` |
| Бот падает | Убедитесь что `Restart=always` в systemd |
| Rate limit | Увеличьте `RATE_LIMIT_SECONDS` |
| Не видит переменные | Проверьте `.env` файл рядом с `main.py` |

---

<p align="center">
  <sub>Made with ❤️ by <a href="https://github.com/Straiko">Straiko</a></sub>
</p>
