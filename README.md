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
2. Create a channel (or reuse one). Add the bot as an administrator with permission to see members, otherwise `get_chat_member` will fail.
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
WEBAPP_URL=
WEBAPP_HOST=0.0.0.0
WEBAPP_PORT=8000
WEBAPP_SERVE=true
WEBAPP_DEBUG=false
```

- `BOT_TOKEN` — token from BotFather.
- `SUPER_ADMIN_ID` — your Telegram ID. The first `/start` from this user grants `super_admin`.
- `CHANNEL_ID` — numeric channel ID, including the leading minus.
- `WEBAPP_URL` — public **https** URL of the Mini App, including `/webapp/`. Leave empty until the site is reachable over HTTPS. Telegram rejects `http://` and placeholders like `yourdomain.com`.
- `WEBAPP_HOST` / `WEBAPP_PORT` — where FastAPI listens. Default is `0.0.0.0:8000`.
- `WEBAPP_SERVE` — `true` starts FastAPI inside the same process as the bot (`python -m app.bot`).
- `WEBAPP_DEBUG` — local-only. When `true`, API requests may send `X-Debug-Telegram-Id` instead of Telegram `initData`. Keep `false` on a public tunnel.

Settings are loaded with pydantic-settings. Secrets stay out of source code.

### 5. Run the bot (chat only)

From the project root with the virtualenv active:

```powershell
python -m app.bot
```

Write `/start` to the bot in Telegram. `tea_shop.db` is created automatically.

The chat catalog and cart work without the Mini App. The reply button **Открыть витрину** appears only after `WEBAPP_URL` is a real `https://` address.

## Telegram Mini App (the website)

Telegram opens Mini Apps only over **HTTPS with a valid certificate**. `http://localhost:8000` cannot be used as `WEBAPP_URL` on a phone.

Two ways to raise the site:

1. **Windows / local test** — FastAPI on port 8000 + Cloudflare Tunnel (quick HTTPS URL).
2. **Production** — your domain, nginx (or similar), Let's Encrypt, then the same FastAPI process.

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

Then in the bot chat send `/start` so the reply keyboard refreshes. Open the storefront from **Витрина** or **Открыть витрину**, not by pasting the Cloudflare link into a normal browser. A regular browser has no Telegram `initData`; the catalog can still load, but cart and checkout need a real Mini App session.

### 5. Production domain

On a server with a real certificate you do not need a tunnel.

1. Point `shop.example.com` at the machine.
2. Build the frontend on the server (`cd frontend && npm ci && npm run build`).
3. Run `python -m app.bot` (or the systemd unit below). FastAPI listens on `127.0.0.1:8000` if you set `WEBAPP_HOST=127.0.0.1`.
4. Reverse-proxy with TLS. Example nginx:

```nginx
server {
    listen 443 ssl;
    server_name shop.example.com;

    ssl_certificate     /etc/letsencrypt/live/shop.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shop.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

5. `.env`:

```env
WEBAPP_URL=https://shop.example.com/webapp/
WEBAPP_HOST=127.0.0.1
WEBAPP_PORT=8000
WEBAPP_SERVE=true
```

6. Put the same `https://shop.example.com/webapp/` into BotFather **Menu Button** and **Main App**. Domain: `shop.example.com`.

### API routes

| Method | Path | Auth |
| --- | --- | --- |
| `GET` | `/webapp/`, `/webapp` | public (React app) |
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

## Server install (Ubuntu)

### 1. System packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx certbot python3-certbot-nginx
python3 --version
```

Install Node.js 20+ for the Mini App build (NodeSource or the distro package). Then, after the clone and venv steps, build the UI:

```bash
sudo -u teabot -H bash -lc 'cd /opt/tea-bot/frontend && npm ci && npm run build'
```

Python 3.11+ is required. Ubuntu 22.04 already has it.

### 2. Service user

```bash
sudo adduser --system --group --home /opt/tea-bot teabot
sudo mkdir -p /opt/tea-bot
sudo chown teabot:teabot /opt/tea-bot
```

Clone the repository into `/opt/tea-bot`, then:

```bash
sudo -u teabot -H bash -lc 'cd /opt/tea-bot && python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt'
```

### 3. Secrets

```bash
sudo -u teabot cp /opt/tea-bot/Example.env /opt/tea-bot/.env
sudo -u teabot nano /opt/tea-bot/.env
sudo chmod 600 /opt/tea-bot/.env
```

### 4. systemd unit

Create `/etc/systemd/system/tea-bot.service`:

```ini
[Unit]
Description=Tea shop Telegram bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=teabot
Group=teabot
WorkingDirectory=/opt/tea-bot
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/tea-bot/.venv/bin/python -m app.bot
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tea-bot
sudo systemctl status tea-bot
sudo journalctl -u tea-bot -f
```

Run a single polling process per token. The reminder scheduler and, when `WEBAPP_SERVE=true`, the Mini App API live in the same process. Put the public `https://…/webapp/` URL in `.env` and in BotFather after nginx has a certificate.

### 5. Updates

```bash
cd /opt/tea-bot
sudo -u teabot git pull
sudo -u teabot /opt/tea-bot/.venv/bin/pip install -r requirements.txt
sudo -u teabot -H bash -lc 'cd /opt/tea-bot/frontend && npm ci && npm run build'
sudo systemctl restart tea-bot
```

Keep `tea_shop.db`. It stores users, products, and orders.

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

- `subscription.py` — `get_chat_member` for `CHANNEL_ID` and a channel URL.
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
3. Main menu: **Открыть витрину** (Mini App), **Catalog**, **Cart**, **My orders**, **Contact admin**. The menu button **Витрина** opens the same Web App.
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
- After changing the tunnel or domain, update `.env`, BotFather, restart the bot, and send `/start`.
- For higher load, point `DATABASE_URL` at PostgreSQL. The repository layer does not have to change.
