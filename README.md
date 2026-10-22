# Tea Shop Telegram Bot

A Telegram storefront and lightweight CRM for selling specialty tea.

The bot covers three business jobs:

1. **Sales.** Customers browse photo cards, open a hidden composition on demand, add items to a cart, and place an order. The cart snapshot is stored with the price at purchase time.
2. **Retention.** If a cart is left unpaid, the bot reminds the user after 2 hours and 12 hours. After 24 hours the cart is cleared automatically.
3. **Team management.** The super admin issues one-time invite links. Regular admins add products, review orders, and change fulfillment status. Every new order is delivered to all `admin` and `super_admin` users in private chat.

Storefront access requires a subscription to the channel from `.env`. Admins and the super admin skip that check.

The same shop is also a **Telegram Mini App**: a React storefront (catalog, cart, checkout, orders) served by FastAPI. The bot and the Mini App share one SQLite database and the same SQLAlchemy models. After checkout, FastAPI calls the existing `place_order` service so the customer and the admins still get Telegram messages.

## Tech stack

| Layer | Tool |
| --- | --- |
| Telegram Bot API | aiogram 3.4.1 |
| Mini App API | FastAPI, Uvicorn |
| Mini App UI | React, Vite, Tailwind CSS, `@twa-dev/sdk` |
| Database | SQLite via aiosqlite |
| ORM | SQLAlchemy 2.0 async (`select` / `insert` / `update` / `delete`) |
| Settings | pydantic-settings, `.env` |
| Scheduler | APScheduler 3.10 (`AsyncIOScheduler`) |
| Linter | Ruff |
| Language | Python 3.11+, Node.js 20+ (frontend build only) |

The project uses a layered layout: handlers never talk to SQL, repositories stay free of Telegram logic, and services own sales, reminders, roles, and order tracking. FastAPI routers reuse those repositories and services.

## Local setup

### 1. Telegram

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the token.
2. Create a channel (or reuse one). Add the bot as an administrator, otherwise `get_chat_member` fails and nobody passes the subscription check. For a private channel also allow **Add subscribers** (invite users), so the bot can give out an invite link.
3. Get the numeric channel ID (`-100...`). That value belongs in `.env`.
4. Get your Telegram user ID (for example via `@userinfobot`). That value is `SUPER_ADMIN_ID`.

### 2. Python on Windows

1. Install Python 3.11 or newer from [python.org](https://www.python.org/downloads/).
2. Enable **Add python.exe to PATH**.
3. Check the install:

```powershell
python --version
```

### 3. Virtual environment

```powershell
git clone https://github.com/M1shut3r/Telegram_Tea_Bot.git
cd Telegram_Tea_Bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation scripts:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

On Linux or macOS:

```bash
git clone https://github.com/M1shut3r/Telegram_Tea_Bot.git
cd Telegram_Tea_Bot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Environment file

Copy the example file and fill in real values. Do not commit `.env`.

```powershell
copy Example.env .env
```

```bash
cp Example.env .env
```

```env
BOT_TOKEN=123456:ABC-DEF
SUPER_ADMIN_ID=123456789
CHANNEL_ID=-1001234567890
CHANNEL_URL=
WEBAPP_URL=
WEBAPP_HOST=0.0.0.0
WEBAPP_PORT=8000
WEBAPP_SERVE=true
WEBAPP_DEBUG=false
LOG_LEVEL=critical
```

- `BOT_TOKEN` — token from BotFather.
- `SUPER_ADMIN_ID` — your Telegram ID. The first `/start` from this user grants `super_admin`.
- `CHANNEL_ID` — numeric channel ID, including the leading minus. `-1001234567890` is only the example value: the bot refuses it and tells the super admin at startup.
- `CHANNEL_URL` — optional link for the **Подписаться на канал** button (`https://t.me/name`, `@name` or an invite link `https://t.me/+…`). Leave empty to take the link from the channel itself.
- `WEBAPP_URL` — public **https** URL of the Mini App, including `/webapp/`. Leave empty until the site is reachable over HTTPS. Telegram rejects `http://` and placeholders like `yourdomain.com`.
- `WEBAPP_HOST` / `WEBAPP_PORT` — where FastAPI listens. Default is `0.0.0.0:8000`.
- `WEBAPP_SERVE` — `true` starts FastAPI inside the same process as the bot (`python -m app.bot`).
- `WEBAPP_DEBUG` — local-only. When `true`, API requests may send `X-Debug-Telegram-Id` instead of Telegram `initData`. Keep `false` on a public tunnel.
- `LOG_LEVEL` — `critical` hides bot and Uvicorn logs. Set `info` only when you need to debug.

Settings are loaded with pydantic-settings. Secrets stay out of source code.

### 5. Run the bot (chat only)

From the project root with the virtualenv active:

```powershell
python -m app.bot
```

Write `/start` to the bot in Telegram. `tea_shop.db` is created automatically.

The chat catalog and cart work without the Mini App. The Telegram menu button **Витрина** appears only after `WEBAPP_URL` is a real `https://` address.

On startup the bot checks the channel from `CHANNEL_ID`. If the ID is wrong, the bot is not a channel admin, or it cannot get an invite link, the super admin receives a message describing what to fix.

## Telegram Mini App (the website)

Telegram opens Mini Apps only over **HTTPS with a valid certificate**. `http://localhost:8000` cannot be used as `WEBAPP_URL` on a phone.

Two ways to raise the site:

1. **Ubuntu VPS (рекомендуется)** — полный гайд ниже: [Развёртывание на Ubuntu](#развёртывание-на-ubuntu-чистый-сервер). Бот и сайт работают как служба systemd за nginx с HTTPS: на своём домене или без домена, через бесплатный адрес sslip.io.
2. **Windows / локальный тест** — FastAPI на порту 8000 + Cloudflare Tunnel.

### 1. Build the frontend

Install [Node.js LTS](https://nodejs.org/) (20 or newer). On Windows:

```powershell
winget install OpenJS.NodeJS.LTS
```

Close the terminal, open a new one, then:

```powershell
cd frontend
npm install
npm run build
```

The build writes `frontend/dist`. FastAPI serves that folder at `/webapp`. Rebuild after any change in `frontend/src`.

### 2. Start the bot and the API

From the project root, virtualenv active:

```powershell
python -m app.bot
```

With `WEBAPP_SERVE=true` this process also starts Uvicorn on `WEBAPP_PORT` (8000). Leave the window open.

You can run the API alone:

```powershell
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 3. Local HTTPS with Cloudflare Tunnel (Windows)

Telegram will not open `localhost`. A tunnel gives a temporary `https://….trycloudflare.com` URL.

Install the tunnel client:

```powershell
winget install --id Cloudflare.cloudflared
```

Open a **second** PowerShell window. If QUIC is blocked (common on home routers), use HTTP/2:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000 --protocol http2
```

Do not add `--loglevel fatal`: cloudflared prints the tunnel URL at `info` level, so that flag hides it.

Wait for the box:

```text
Your quick Tunnel has been created! Visit it at:
https://random-words.trycloudflare.com
```

That hostname is the site address. Do not close this window.

If you see `Failed to dial a quic connection`, stop with `Ctrl+C` and rerun with `--protocol http2`.

Put the tunnel URL into `.env` (keep the `/webapp/` suffix):

```env
WEBAPP_URL=https://random-words.trycloudflare.com/webapp/
```

Restart the bot (`Ctrl+C` in the first window, then `python -m app.bot` again). The tunnel window stays running.

A new `cloudflared` process creates a **new** hostname. Update `WEBAPP_URL`, BotFather, and restart the bot every time the tunnel URL changes.

### 4. BotFather

`Menu Button` and `Main App` expect a **full URL**, starting with `https://`. If the field suggests `http://`, replace the whole line.

Paste:

```text
https://random-words.trycloudflare.com/webapp/
```

1. [@BotFather](https://t.me/BotFather) → `/mybots` → your bot → **Bot Settings**.
2. **Menu Button** — title `Витрина`, URL as above.
3. **Main App** — the same URL.
4. If you see a **Domain** field, send only the host, no scheme and no path: `random-words.trycloudflare.com`.

On startup the bot also calls `set_chat_menu_button`, so a **Витрина** button appears next to the message field.

Then in the bot chat send `/start` so the reply keyboard refreshes. Open the storefront from **Витрина**, not by pasting the Cloudflare link into a normal browser. A regular browser has no Telegram `initData`; the catalog can still load, but cart and checkout need a real Mini App session.

### API routes

| Method | Path | Auth |
| --- | --- | --- |
| `GET`, `HEAD` | `/webapp/`, `/webapp` | public (React app) |
| `GET` | `/api/products` | public |
| `GET` | `/api/products/{id}/photo` | public (proxies the Telegram file) |
| `GET` | `/api/cart` | Telegram `initData` |
| `POST` | `/api/cart/add` | Telegram `initData` |
| `POST` | `/api/cart/quantity` | Telegram `initData` |
| `GET` | `/api/orders` | Telegram `initData` |
| `POST` | `/api/orders/checkout` | Telegram `initData` |

Checkout writes the order through `place_order`: the cart is cleared, the customer gets «заказ принят», and every admin receives the order card.

### Frontend dev server (optional)

```powershell
cd frontend
npm run dev
```

Vite listens on `http://127.0.0.1:5173` and proxies `/api` to port 8000. Telegram still needs the HTTPS tunnel (or your domain) pointed at that stack. For day-to-day Mini App testing, prefer `npm run build` and the bot process.

## Linting

Install development tools and run Ruff:

```powershell
pip install -r requirements-dev.txt
ruff check app api
ruff format app api
```

CI runs the same checks on every push and pull request.

## Развёртывание на Ubuntu (чистый сервер)

Гайд для **пустого** Ubuntu 22.04 или 24.04: на машине ещё нет Python-проекта, Node, бота и сайта.

Итог:

| Что | Как работает |
| --- | --- |
| Бот и сайт Mini App | Служба systemd `tea-bot`: один процесс `python -m app.bot`, FastAPI на `127.0.0.1:8000`. Запускается вместе с сервером и перезапускается после сбоя. |
| HTTPS для Telegram | nginx и бесплатный сертификат Let's Encrypt. certbot продлевает его сам. |
| Адрес сайта | Свой домен или бесплатный адрес `IP-через-дефисы.sslip.io`. Покупать домен не обязательно. |

`screen` и туннель не нужны. Быстрый туннель Cloudflare остался только как временный вариант для сервера без публичного IP: [шаг 16](#16-временный-вариант-быстрый-туннель-cloudflare).

### 0. Что нужно до входа на сервер

1. VPS с Ubuntu, публичным IP и SSH-доступом (логин вроде `ubuntu` или `root`).
2. Бот в [@BotFather](https://t.me/BotFather): скопируйте токен.
3. Канал: добавьте бота администратором с правом видеть участников.
4. Числовой ID канала (`-100…`) и свой Telegram ID (`SUPER_ADMIN_ID`, например через `@userinfobot`).
5. Адрес сайта, один из двух:
   - **Без домена:** IP сервера через дефисы плюс `.sslip.io`. Для IP `203.0.113.10` это `203-0-113-10.sslip.io`. Сервис [sslip.io](https://sslip.io) сам направляет такое имя на IP из названия, регистрироваться нигде не нужно. Адрес не меняется, пока у сервера тот же IP.
   - **Свой домен:** у регистратора создайте A-запись (например, `shop.example.com`) со значением IP сервера.

Дальше все команды — **на сервере**, в SSH. Вместо `203-0-113-10.sslip.io` подставляйте свой адрес.

### 1. Подключиться по SSH

С своего компьютера:

```bash
ssh ubuntu@IP_СЕРВЕРА
```

Подставьте свой логин и IP. Если зашли как `root`, `sudo` в командах ниже можно не писать.

### 2. Обновить систему

```bash
sudo apt update
sudo apt upgrade -y
```

Если установщик спросит про перезапуск служб — подтвердите. После большого обновления ядра лучше перезагрузить сервер и зайти по SSH снова:

```bash
sudo reboot
```

### 3. Поставить пакеты

```bash
sudo apt install -y python3 python3-venv python3-pip git curl ca-certificates ufw nginx certbot python3-certbot-nginx
python3 --version
```

Нужен Python **3.11 или новее**. На Ubuntu 22.04 и 24.04 он уже есть.

Если apt пишет `404 Not Found` на какой-то пакет (например, nginx), значит, на сервере устарел список пакетов: Ubuntu уже заменила эту версию новой. Обновите список с нуля и повторите установку:

```bash
sudo dpkg --configure -a
sudo rm -rf /var/lib/apt/lists/*
sudo apt -o Acquire::ForceIPv4=true update
sudo apt -o Acquire::ForceIPv4=true install -y -f python3 python3-venv python3-pip git curl ca-certificates ufw nginx certbot python3-certbot-nginx
```

Удалять `/var/lib/apt/lists` безопасно: это кэш, `apt update` скачает его заново.

### 4. Поставить Node.js 20 (сборка витрины)

Пакет `nodejs` из Ubuntu 22.04 слишком старый. Ставим 20.x:

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version
```

`node` должен показать `v20…`.

### 5. Скачать проект

```bash
cd ~
git clone https://github.com/M1shut3r/Telegram_Tea_Bot.git
cd ~/Telegram_Tea_Bot
```

Дальше все пути — из этой папки.

### 6. Python-окружение и зависимости

```bash
cd ~/Telegram_Tea_Bot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

В начале строки должно появиться `(.venv)`. Службе активировать venv не нужно, она запускает Python прямо из `.venv`. Активируйте его только для ручных команд (`pip install`, скрипты из `app.tools`).

### 7. Собрать сайт (React → `frontend/dist`)

```bash
cd ~/Telegram_Tea_Bot/frontend
npm ci
npm run build
cd ~/Telegram_Tea_Bot
```

Без этой папки FastAPI отдаст «Mini App не собран». После правок в `frontend/src` снова выполните `npm run build`.

### 8. Файл `.env`

```bash
cd ~/Telegram_Tea_Bot
cp Example.env .env
nano .env
```

Заполните так:

```env
BOT_TOKEN=123456:ABC-DEF
SUPER_ADMIN_ID=123456789
CHANNEL_ID=-1001234567890
CHANNEL_URL=
WEBAPP_URL=https://203-0-113-10.sslip.io/webapp/
WEBAPP_HOST=127.0.0.1
WEBAPP_PORT=8000
WEBAPP_SERVE=true
WEBAPP_DEBUG=false
LOG_LEVEL=critical
```

- `CHANNEL_ID` — числовой ID **вашего** канала. `-1001234567890` — только пример: с ним бот при запуске пришлёт супер-админу предупреждение.
- `CHANNEL_URL` — необязательно. Ссылка для кнопки «Подписаться на канал» (`https://t.me/имя`, `@имя` или приглашение `https://t.me/+…`). Если пусто, бот берёт ссылку из самого канала.
- `WEBAPP_URL` — ваш адрес из шага 0 с `https://` в начале и `/webapp/` в конце. Слеш в конце обязателен.
- `WEBAPP_HOST=127.0.0.1` — сайт слушает только локально. Снаружи к нему ходит nginx, порт 8000 в интернет не открывается.

Сохранить в nano: `Ctrl+O`, Enter, выйти: `Ctrl+X`.

```bash
chmod 600 .env
```

### 9. Файрвол

Открываем SSH и веб-порты 80 и 443 для nginx:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
sudo ufw status
```

Если `ufw` пишет `Could not find a profile matching 'Nginx Full'`, значит, nginx не установился. Вернитесь к шагу 3. Если у хостинга есть свой файрвол в панели управления, откройте в нём порты 80 и 443.

### 10. Бот как служба systemd

```bash
APP_DIR=$HOME/Telegram_Tea_Bot
sudo tee /etc/systemd/system/tea-bot.service > /dev/null <<EOF
[Unit]
Description=Tea shop bot and Mini App
After=network-online.target
Wants=network-online.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/python -m app.bot
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now tea-bot
systemctl status tea-bot --no-pager
curl -I http://127.0.0.1:8000/webapp/
```

✅ В статусе `active (running)`, `curl` показывает `HTTP/1.1 200`. Если сразу после запуска пришло что-то другое, подождите 5 секунд и повторите `curl`.

Если служба не `active (running)` (например, `activating (auto-restart)` или `failed`), бот падает при запуске. Причина — в логе:

```bash
journalctl -u tea-bot -n 40 --no-pager
```

Один токен — один процесс. Пока служба работает, не запускайте `python -m app.bot` вручную, иначе два бота будут мешать друг другу.

### 11. nginx

```bash
DOMAIN=203-0-113-10.sslip.io
getent hosts $DOMAIN
```

✅ Команда выводит IP сервера. Если пусто или IP чужой, проверьте адрес (шаг 0) и подождите, пока обновится DNS. Если вы переподключились по SSH, строку `DOMAIN=…` выполните снова.

```bash
sudo tee /etc/nginx/sites-available/tea-bot > /dev/null <<'EOF'
server {
    listen 80;
    server_name DOMAIN_HERE;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
sudo sed -i "s/DOMAIN_HERE/$DOMAIN/" /etc/nginx/sites-available/tea-bot
sudo ln -sf /etc/nginx/sites-available/tea-bot /etc/nginx/sites-enabled/tea-bot
sudo nginx -t && sudo systemctl reload nginx
curl -I http://$DOMAIN/webapp/
```

✅ `nginx -t` пишет `syntax is ok`, `curl` показывает `HTTP/1.1 200`. Ответ `502 Bad Gateway` значит, что nginx работает, но бот не запущен: вернитесь к шагу 10.

### 12. HTTPS-сертификат

```bash
sudo certbot --nginx -d $DOMAIN
curl -I https://$DOMAIN/webapp/
```

certbot спросит почту для уведомлений, согласие с условиями (`Y`) и рассылку (можно `N`). Он сам включит HTTPS в конфиге nginx и будет продлевать сертификат автоматически. Проверить продление: `sudo certbot renew --dry-run`.

✅ `Successfully deployed certificate`, затем `HTTP/1.1 200` по `https://`.

Если certbot не может проверить домен, убедитесь, что `getent hosts $DOMAIN` выводит IP сервера и порт 80 открыт (шаг 9).

### 13. BotFather

1. [@BotFather](https://t.me/BotFather) → `/mybots` → ваш бот → **Bot Settings**.
2. **Main App** — полный URL: `https://203-0-113-10.sslip.io/webapp/`.
3. Поле **Domain** — только адрес, без `https://` и без пути: `203-0-113-10.sslip.io`.

Кнопку меню **Витрина** бот выставляет сам при каждом запуске из `WEBAPP_URL`.

В чате с ботом отправьте `/start`. Витрину открывайте кнопкой **Витрина** рядом с полем ввода, не вставкой ссылки в обычный браузер: там нет `initData`, корзина не заработает.

### 14. Повседневные команды

| Действие | Команда |
| --- | --- |
| Работает ли бот | `systemctl status tea-bot` |
| Логи в реальном времени (выход: `Ctrl+C`) | `journalctl -u tea-bot -f` |
| Перезапустить | `sudo systemctl restart tea-bot` |
| Остановить / запустить | `sudo systemctl stop tea-bot` / `sudo systemctl start tea-bot` |
| Проверить сайт | `curl -I https://$DOMAIN/webapp/` |

При `LOG_LEVEL=critical` бот почти ничего не пишет в лог. Для разбора проблемы поставьте в `.env` `LOG_LEVEL=info`, выполните `sudo systemctl restart tea-bot` и смотрите `journalctl -u tea-bot -f`. Потом верните `critical`.

Обновить код с GitHub (база `tea_shop.db` не удаляется):

```bash
cd ~/Telegram_Tea_Bot
git pull
source .venv/bin/activate
pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
sudo systemctl restart tea-bot
```

Если в обновлении изменился только Python-код, достаточно `git pull` и `sudo systemctl restart tea-bot`.

После перезагрузки VPS ничего делать не нужно: nginx и `tea-bot` запускаются сами.

### 15. Если что-то не работает

| Что видно | Причина | Что делать |
| --- | --- | --- |
| `502 Bad Gateway` | nginx работает, бот не запущен или падает | `systemctl status tea-bot`, затем `journalctl -u tea-bot -n 40 --no-pager` |
| Витрина: «Не удалось выполнить запрос» | Запрос не дошёл до приложения: бот не работает или сайт недоступен | `curl -I https://$DOMAIN/webapp/` и `systemctl status tea-bot`. Затем закройте витрину и откройте снова кнопкой **Витрина** |
| Витрина: «Недействительные данные Telegram» | Витрина открыта не из Telegram или сессии больше суток | Закройте витрину и откройте снова кнопкой **Витрина** |
| `404 Not Found` при `apt install` | Устарел список пакетов | Шаг 3, блок с `rm -rf /var/lib/apt/lists/*` |
| `Could not find a profile matching 'Nginx Full'` | nginx не установился | Шаг 3 |
| Вместо фото товара буква **Ж** или «Фото временно недоступно» | Фото добавлены через другой бот (сменился токен) | `python -m app.tools.recover_photos`, см. [Operations](#operations) |
| Бот не видит подписку на канал | Новый бот не админ канала | Добавьте бота администратором канала |
| Кнопка «Подписаться на канал» ведёт не туда или её нет | Неверный `CHANNEL_ID` в `.env`, бот не в канале, или у закрытого канала боту не дали права приглашать | Смотрите сообщение, которое бот присылает супер-админу при запуске. Можно задать ссылку вручную в `CHANNEL_URL` |

### 16. Временный вариант: быстрый туннель Cloudflare

Только для сервера без публичного IP или для короткой проверки. Быстрый туннель Cloudflare даёт без гарантий работы, а его адрес меняется при каждом перезапуске `cloudflared` и после обрыва связи. В Telegram это выглядит как `ERR_NAME_NOT_RESOLVED` или «Не удалось выполнить запрос». Для постоянной работы используйте шаги 9–13.

```bash
sudo apt install -y screen
curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i /tmp/cloudflared.deb
screen -S tea-site
cloudflared tunnel --url http://127.0.0.1:8000 --protocol http2 2>&1 | tee ~/tea-tunnel.log
```

На ARM-сервере вместо `amd64` скачайте `cloudflared-linux-arm64.deb`. Не добавляйте `--loglevel fatal`: адрес туннеля cloudflared печатает на уровне `info`, и с этим флагом он не появится.

Дождитесь блока `Your quick Tunnel has been created!` и отсоединитесь: `Ctrl+A`, затем `D`. Бот при этом работает как служба (шаг 10), nginx и certbot не нужны. Пропишите адрес туннеля в бота:

```bash
cd ~/Telegram_Tea_Bot
NEW=$(grep -oE 'https://[a-z0-9]+(-[a-z0-9]+)+\.trycloudflare\.com' ~/tea-tunnel.log | tail -1); echo "$NEW"
sed -i "s#^WEBAPP_URL=.*#WEBAPP_URL=$NEW/webapp/#" .env
sudo systemctl restart tea-bot
```

Затем обновите **Main App** и **Domain** в BotFather (шаг 13) и отправьте боту `/start`. Всё это придётся повторять при каждой смене адреса туннеля.

## Project layout

```text
.
├── Example.env
├── .env
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── README.md
├── tea_shop.db
├── app/                 # Telegram bot
│   ├── bot.py           # polling, Uvicorn, menu button
│   ├── config.py
│   ├── database.py      # shared engine and SessionMaker
│   ├── models/          # shared SQLAlchemy models
│   ├── repositories/
│   ├── services/
│   ├── handlers/
│   └── keyboards/
├── api/                 # FastAPI for the Mini App
│   ├── main.py          # CORS, /webapp, /favicon.ico
│   ├── deps.py          # session + Telegram initData
│   ├── schemas.py
│   └── routers/         # products, cart, orders
└── frontend/            # React Mini App (Vite)
    ├── src/
    └── dist/            # created by npm run build
```

### models

Tables and relations only.

- `users` — `telegram_id`, `username`, role `user` / `admin` / `super_admin`.
- `products` — name, Telegram `photo_id`, description, composition, price, active flag.
- `carts` — user, product, quantity, created time. Unique per user-product pair.
- `orders` — customer name, phone, country, city, address, total, status, created time.
- `order_items` — purchased items and price at checkout.
- `admin_invites` — one-time uuid token, creator, consumer.

### repositories

Async SQLAlchemy 2.0 CRUD. The base class covers `get`, `create` (`insert`), `update_by_id` (`update`), and `delete_by_id` (`delete`). Specialized repositories load active products, carts with products, orders with items, and invites by token.

### services

- `subscription.py` — `get_chat_member` for `CHANNEL_ID`, the channel link (`CHANNEL_URL`, public username or the bot's invite link, cached for 10 minutes) and the startup self-check.
- `cart_lifecycle.py` — 2h / 12h / 24h jobs, cancel on checkout or manual clear, restore after restart.
- `ordering.py` — totals, `Order` + `OrderItems`, admin broadcast, first customer notification.
- `order_tracking.py` — status titles, customer notifications, roadmap text.
- `admin_manager.py` — uuid invites, deep-link activation, role changes, `HasRole` filter.

### handlers

aiogram 3.x routers. The database session is injected by middleware.

- `start.py` — `/start`, `invite_<token>` deep links, subscription gate, contact-admin button.
- `catalog.py` — product carousel with photo, composition toggle, add to cart.
- `cart.py` — quantity controls, cart clear, checkout FSM: name → phone → country → city → address.
- `orders.py` — "My orders" list and status roadmap.
- `admin.py` — product create FSM and order status updates.
- `super_admin.py` — invite links and admin revocation.

### keyboards

Keyboard builders stay out of handlers so button labels and callback data stay in one place.

## Customer features

1. `/start` registers the user and can activate an admin invite.
2. Unsubscribed users see **Subscribe** and **I subscribed**.
3. Main menu: **Catalog**, **Cart**, **My orders**, **Contact support**. The Mini App opens from Telegram's own menu button **Витрина** next to the message field.
4. Catalog is a photo carousel with previous / next, composition, and add-to-cart.
5. Cart supports plus/minus, clear, and checkout. Quantity edits update the same message.
6. Checkout collects full name, phone, country (Russia), city, and street address.
7. After checkout the cart is cleared, reminder jobs are cancelled, and admins receive the request.
8. **My orders** shows a vertical status roadmap (`in_progress` → `packed` → `shipped`).
9. Cancel checkout with **Cancel** or `/cancel`.

Reminders:

| Delay | Action |
| --- | --- |
| 2 hours | Soft reminder to finish the order |
| 12 hours | Second reminder, cleanup warning |
| 24 hours | Cart is deleted and the user is notified |

The timer starts when the cart becomes non-empty. Adding more items does not reset it. Checkout, manual clear, or a zero quantity cancel the jobs. Abandoned carts are restored after a process restart.

## Admin features

| Role | How it is granted | What it can do |
| --- | --- | --- |
| `user` | anyone who writes the bot | storefront, cart, orders |
| `admin` | one-time invite from the super admin | products, order list, status changes, inbound order alerts |
| `super_admin` | `SUPER_ADMIN_ID` in `.env` | everything an admin can do, plus invites and role removal |

Order statuses: `new` → `in_progress` → `packed` → `shipped` → `done`.

A regular admin (**Admin panel**):

- adds a product in steps: name, photo, description, hidden composition, price;
- opens an order card and moves it through fulfillment statuses;
- each status change updates the admin message and notifies the customer.

The super admin (**Super admin**):

- creates `https://t.me/<bot>?start=invite_<token>` links;
- lists the team;
- demotes a regular admin back to `user`. The super admin cannot be demoted.

Admins must send `/start` at least once, otherwise Telegram will not deliver bot messages to them.

## Operations

- Never commit `.env` or `tea_shop.db`. Use `Example.env` as the template.
- The bot must be a channel administrator.
- One polling process per token.
- Reminder jobs live in process memory and are rebuilt from open carts on startup.
- Mini App `WEBAPP_URL` must be `https://…/webapp/`. Both `/webapp` and `/webapp/` serve the app without a redirect (a 307 used to drop Telegram `initData`).
- After changing the domain (or the tunnel address), update `WEBAPP_URL` in `.env` and BotFather, restart the bot (`sudo systemctl restart tea-bot` on the server), and send `/start`.
- Product photos are stored as Telegram `file_id`, which works only in the bot that received the photo. After switching to a new bot token, the catalog re-uploads photos cached by the Mini App and saves the new ids. Products without a cached copy show a text card (and **Ж** in the Mini App) until the photo is restored. Run `python -m app.tools.recover_photos` while the bot keeps running: it lists every product's photo status and, given the old bot token at the prompt, downloads the missing photos into the cache. `.env` and the database stay unchanged. Anything still missing needs a new photo from an admin (**Админ-панель** → **Редактировать товар** → **Фото**). Add the new bot as a channel administrator, otherwise the subscription check fails for regular users.
- For higher load, point `DATABASE_URL` at PostgreSQL. The repository layer does not have to change.
