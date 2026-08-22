# Tea Shop Telegram Bot

A Telegram storefront and lightweight CRM for selling specialty tea.

The bot covers three business jobs:

1. **Sales.** Customers browse photo cards, open a hidden composition on demand, add items to a cart, and place an order. The cart snapshot is stored with the price at purchase time.
2. **Retention.** If a cart is left unpaid, the bot reminds the user after 2 hours and 12 hours. After 24 hours the cart is cleared automatically.
3. **Team management.** The super admin issues one-time invite links. Regular admins add products, review orders, and change fulfillment status. Every new order is delivered to all `admin` and `super_admin` users in private chat.

Storefront access requires a subscription to the channel from `.env`. Admins and the super admin skip that check.

## Tech stack

| Layer | Tool |
| --- | --- |
| Telegram Bot API | aiogram 3.4.1 |
| Database | SQLite via aiosqlite |
| ORM | SQLAlchemy 2.0 async (`select` / `insert` / `update` / `delete`) |
| Settings | pydantic-settings, `.env` |
| Scheduler | APScheduler 3.10 (`AsyncIOScheduler`) |
| Linter | Ruff |
| Language | Python 3.11+ |

The project uses a layered layout: handlers never talk to SQL, repositories stay free of Telegram logic, and services own sales, reminders, roles, and order tracking.

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
```

- `BOT_TOKEN` — token from BotFather.
- `SUPER_ADMIN_ID` — your Telegram ID. The first `/start` from this user grants `super_admin`.
- `CHANNEL_ID` — numeric channel ID, including the leading minus.

Settings are loaded with pydantic-settings. Secrets stay out of source code.

### 5. Run

From the project root with the virtualenv active:

```powershell
python -m app.bot
```

Write `/start` to the bot in Telegram. `tea_shop.db` is created automatically.

## Linting

Install development tools and run Ruff:

```powershell
pip install -r requirements-dev.txt
ruff check app
ruff format app
```

CI runs the same checks on every push and pull request.

## Server install (Ubuntu)

### 1. System packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
python3 --version
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

Run a single polling process per token. The reminder scheduler lives in the same process.

### 5. Updates

```bash
cd /opt/tea-bot
sudo -u teabot git pull
sudo -u teabot /opt/tea-bot/.venv/bin/pip install -r requirements.txt
sudo systemctl restart tea-bot
```

Keep `tea_shop.db`. It stores users, products, and orders.

## Project layout

```text
.
├── Example.env          # template, safe to commit
├── .env                 # real secrets, never commit
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml       # Ruff config
├── README.md
├── tea_shop.db          # created on first run
└── app/
    ├── bot.py           # polling, middleware, APScheduler
    ├── config.py        # Settings from .env
    ├── database.py      # engine, AsyncSession, session middleware
    ├── models/          # SQLAlchemy models
    ├── repositories/    # CRUD
    ├── services/        # business use cases
    ├── handlers/        # aiogram routers
    └── keyboards/       # Reply and Inline keyboards
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
3. Main menu: **Catalog**, **Cart**, **My orders**, **Contact admin**.
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
- For higher load, point `DATABASE_URL` at PostgreSQL. The repository layer does not have to change.
