# 🚀 Деплой SHK Bot

## Локальный запуск

```bash
git clone https://github.com/Straiko/shk.git
cd shk
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Вписать BOT_TOKEN
python main.py
```

## VPS / Выделенный сервер

### 1. Подключение к серверу

```bash
ssh user@your-server-ip
```

### 2. Установка зависимостей

```bash
sudo apt update && sudo apt install -y python3 python3-venv git
git clone https://github.com/Straiko/shk.git
cd shk
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Настройка .env

```bash
cp .env.example .env
nano .env
```

Заполнить:
- `BOT_TOKEN` — токен от @BotFather
- `OCR_API_KEY` — ключ OCR.space (или оставить `helloworld`)
- `ADMIN_USER_ID` — ваш Telegram ID

### 4. systemd сервис (автозапуск)

```bash
sudo nano /etc/systemd/system/shk-bot.service
```

```ini
[Unit]
Description=SHK Bot — сканер штрих-кодов
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
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable shk-bot
sudo systemctl start shk-bot
```

### 5. Команды управления

```bash
sudo systemctl status shk-bot    # статус
sudo systemctl restart shk-bot   # перезапуск
sudo systemctl stop shk-bot      # остановка
sudo journalctl -u shk-bot -f    # логи в реальном времени
```

## Docker

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### Сборка и запуск

```bash
docker build -t shk-bot .
docker run -d --name shk-bot --restart unless-stopped --env-file .env shk-bot
```

### docker-compose.yml

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

## Render (бесплатный хостинг)

1. Создать аккаунт на [render.com](https://render.com)
2. New → Background Worker
3. Подключить GitHub репозиторий `Straiko/shk`
4. Настройки:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
5. Добавить переменные окружения в настройках сервиса:
   - `BOT_TOKEN`
   - `OCR_API_KEY`
   - `ADMIN_USER_ID`
6. Deploy

## Railway

```bash
# Установить CLI
npm install -g @railway/cli

# Войти
railway login

# Инициализировать проект
railway init

# Добавить переменные
railway variables set BOT_TOKEN=your_token
railway variables set ADMIN_USER_ID=your_id

# Деплой
railway up
```

## Проверка работоспособности

```bash
# Проверить, что бот отвечает
curl -s "https://api.telegram.org/botYOUR_TOKEN/getMe" | python3 -m json.tool

# Проверить логи
tail -f bot.log
```

## Частые проблемы

| Проблема | Решение |
|----------|---------|
| Бот не отвечает | Проверить `BOT_TOKEN` в `.env` |
| `ModuleNotFoundError` | Активировать venv: `source venv/bin/activate` |
| Ошибка SQLite | Проверить права на файл `data/bot.db` |
| Бот падает через время | Проверить `Restart=always` в systemd |
| Rate limit срабатывает | Увеличить `RATE_LIMIT_SECONDS` |
