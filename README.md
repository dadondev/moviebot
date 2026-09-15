# 🎬 Uzbek Telegram Movie Bot

A production-ready, Uzbek-language Telegram movie catalog and delivery bot built with
**aiogram 3.x**, **PostgreSQL**, **SQLAlchemy 2.x**, **Alembic**, and **Redis**.

Movies are stored in a **private Telegram channel** and delivered to users via Telegram's
`copyMessage` API — the storage channel is never exposed to end users.

---

## ✨ Features

- 🎬 **Movie catalog** — code search, title search, genres, popular & new movies
- 🔢 **Numeric movie codes** — send `125` to get a movie
- 📢 **Mandatory channels** — enforce subscription before movie access
- ⭐ **Favorites & ratings** — 1–5 star ratings, per-user favorites
- 📩 **Movie requests** — users request movies, admins get notified
- 🛠 **Full admin panel** — upload movies, manage channels/genres/users, statistics, broadcast
- 🔒 **Private storage channel** — movies copied via `copyMessage`, never forwarded
- 🚀 **Scalable** — Redis-backed FSM, rate limiting, subscription caching

---

## 🏗 Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Language   | Python 3.12+                        |
| Framework  | aiogram 3.x                         |
| Database   | PostgreSQL                          |
| ORM        | SQLAlchemy 2.x (async)              |
| Migrations | Alembic                             |
| Cache/FSM  | Redis                               |
| Config     | Pydantic Settings                   |
| Container  | Docker / Docker Compose             |
| Testing    | pytest                              |
| Linting    | Ruff                                |

---

## 📁 Project Structure

```
movie-bot/
├── app/
│   ├── bot/
│   │   ├── handlers/          # user + admin handlers
│   │   ├── keyboards/         # inline & reply keyboards
│   │   ├── middlewares/       # registration, rate limiting
│   │   ├── states/            # FSM states
│   │   └── filters/           # admin filter, movie filter
│   ├── database/
│   │   ├── models/            # SQLAlchemy models
│   │   ├── repositories/      # data access layer
│   │   └── database.py        # engine & session
│   ├── services/              # business logic
│   ├── config.py              # settings
│   ├── logging.py             # logging setup
│   └── main.py                # entry point
├── alembic/                   # migrations
├── tests/                     # pytest tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start (Docker)

1. **Clone & configure**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in:
   - `BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
   - `ADMIN_IDS` — your Telegram user IDs (comma-separated)
   - `STORAGE_CHANNEL_ID` — your private channel ID (e.g. `-1001234567890`)

2. **Create the private storage channel**
   - Create a private Telegram channel.
   - Add your bot as an **administrator (with post permission).
   - Get the channel ID (e.g. via `@userinfobot` or by forwarding a message).

3. **Run**

   ```bash
   docker compose up -d --build
   ```

   Migrations run automatically on startup via the entrypoint.

4. **Run migrations manually (if not using Docker)**

   ```bash
   alembic upgrade head
   ```

---

## 🧪 Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

---

## 🛠 Admin Usage

Open the bot and send `/admin` (only for configured `ADMIN_IDS`).

### Upload a movie

1. Tap **➕ Kino qo‘shish**.
2. Send the movie file (video or document) directly to the bot.
3. Follow the FSM prompts (title, original title, code, description, year, genres, country, duration, IMDb, age rating, poster, trailer).
4. Review the preview and tap **✅ Saqlash**.
5. The bot copies the movie to the private storage channel and saves the reference.

### Mandatory channels

1. **📢 Majburiy kanallar** → **➕ Kanal qo‘shish**.
2. Provide the channel username/ID, title, and invite URL.
3. Toggle the whole system with **🔐 Majburiy obuna**.

---

## 🔒 Security Notes

- All secrets come from environment variables — nothing is hardcoded.
- Every admin handler verifies the Telegram user ID server-side.
- Callback data is validated; never trust user-provided callback payloads.
- The storage channel is internal — users only ever receive `copyMessage` output.
- Logging redacts the bot token.

---

## ⚖️ Legal

This bot is designed for media that the administrator has the **legal right or permission**
to distribute. It does not implement scraping or unauthorized redistribution. The Telegram
storage architecture is intended for authorized content only.

---

## 📄 License

For personal/authorized use. Ensure you comply with Telegram's Terms of Service and
applicable copyright law.