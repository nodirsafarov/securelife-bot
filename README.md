# SecureLife — Phishing Detector for Telegram

> An AI-powered Telegram bot that helps ordinary people in Uzbekistan and Central Asia spot phishing in SMS, Telegram messages, emails, and chats — explained in their own language.

[![CI](https://github.com/nodirsafarov/securelife-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/nodirsafarov/securelife-bot/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/github/license/nodirsafarov/securelife-bot)](./LICENSE)

🤖 Live bot: [@securelife_bot](https://t.me/securelife_bot)
🌐 Languages: 🇺🇿 O'zbekcha · 🇬🇧 English

---

## What it does

Anyone can forward or paste a suspicious message to the bot. SecureLife replies with:

- **Verdict** — ✅ SAFE · ⚠️ SUSPICIOUS · 🚨 PHISHING
- **Risk score** — 0 to 100
- **Reasons** — concrete observations from the message itself
- **Advice** — clear actions in the user's language

Built with awareness of local context: Uzcard, Humo, Click, Payme, Kapitalbank, NBU, Hamkorbank, Asaka Bank, government services (`*.gov.uz`, `soliq.uz`, `salym.uz`), telcos, and common scam patterns.

---

## Architecture

```
                ┌──────────────────────┐
   Telegram ───▶│  python-telegram-bot │
                └─────────┬────────────┘
                          ▼
                ┌──────────────────────┐
                │  Handlers + i18n     │
                │  (en / uz)           │
                └─────────┬────────────┘
                          ▼
                ┌──────────────────────┐
                │  Heuristics          │  fast regex pre-checks
                │  (URLs, brands,      │  (no API call yet)
                │   urgency, lures)    │
                └─────────┬────────────┘
                          ▼
                ┌──────────────────────┐
                │  Gemini AI           │  structured JSON verdict
                │  (gemini-2.0-flash)  │  with retries + timeouts
                └─────────┬────────────┘
                          ▼
                ┌──────────────────────┐
                │  Verdict shaper      │  cross-check heuristics,
                │  + i18n template     │  format reply
                └─────────┬────────────┘
                          ▼
                ┌──────────────────────┐
                │  SQLite              │  rate limit + metadata
                │  (no message bodies) │  + language preference
                └──────────────────────┘
```

**Privacy by design:** message contents are never stored — only the user ID, language preference, rate-limit timestamps, and verdict metadata.

---

## Tech stack

- Python 3.11+
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v21 (async)
- [google-generativeai](https://github.com/google-gemini/generative-ai-python) (Gemini API)
- SQLite (built-in, WAL mode)
- python-dotenv, httpx, tldextract

---

## Quick start (development)

### 1. Clone & install

```bash
git clone https://github.com/nodirsafarov/securelife-bot.git
cd securelife-bot

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure secrets

```bash
cp .env.example .env
nano .env   # fill in TELEGRAM_BOT_TOKEN and GEMINI_API_KEY
```

You need:

- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A Gemini API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

> ⚠️ Never commit `.env`. It is already in `.gitignore`.

### 3. Run

```bash
python -m src.main
```

You should see:

```
Starting SecureLife (@securelife_bot) — model=gemini-2.0-flash-exp default_lang=uz rate_limit=30/h
```

Open Telegram, find your bot, send `/start`. Choose a language. Paste any text and watch it analyze.

---

## Deployment

### Option A — Docker (recommended)

```bash
cd deploy
docker compose up -d --build
docker compose logs -f
```

The bot persists its SQLite DB in a Docker volume `bot-data`. To upgrade:

```bash
docker compose pull && docker compose up -d --build
```

### Option B — systemd on a Linux VM

```bash
sudo useradd --system --create-home --shell /sbin/nologin botuser
sudo mkdir -p /opt/securelife-bot && sudo chown -R botuser:botuser /opt/securelife-bot

sudo -u botuser git clone https://github.com/nodirsafarov/securelife-bot.git /opt/securelife-bot
cd /opt/securelife-bot
sudo -u botuser python3.12 -m venv .venv
sudo -u botuser .venv/bin/pip install -r requirements.txt
sudo -u botuser cp .env.example .env
sudo -u botuser nano .env

sudo cp deploy/securelife-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now securelife-bot
sudo systemctl status securelife-bot
sudo journalctl -u securelife-bot -f
```

### Option C — Free always-on hosts

- **Oracle Cloud Always Free** (4 ARM cores, 24 GB RAM, never expires) — recommended for production
- **Fly.io** — easy CLI deployment via the Dockerfile
- **Render / Railway** — works but free tiers have caveats (sleep, build minutes)

---

## Configuration reference

All settings come from environment variables (see [`.env.example`](./.env.example)):

| Variable | Default | What it does |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | required | Token from @BotFather |
| `GEMINI_API_KEY` | required | API key from Google AI Studio |
| `GEMINI_MODEL` | `gemini-2.0-flash-exp` | Gemini model name |
| `BOT_NAME` | `SecureLife` | Display name used in `/start`, `/about` |
| `BOT_USERNAME` | `securelife_bot` | Used in messaging only |
| `RATE_LIMIT_PER_HOUR` | `30` | Per-user message cap |
| `DB_PATH` | `securelife.db` | SQLite path (Docker uses `/data/securelife.db`) |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `DEFAULT_LANGUAGE` | `uz` | `uz` or `en` for new users |
| `ADMIN_USER_IDS` | empty | Comma-separated Telegram IDs allowed to use `/stats` |
| `MAX_INPUT_LENGTH` | `4000` | Reject messages longer than this |

---

## Commands

| Command | Description |
|---|---|
| `/start` | Welcome message; prompts language on first use |
| `/help` | How to use the bot |
| `/about` | About the project |
| `/privacy` | Privacy policy |
| `/language` | Change interface language |
| `/stats` | Aggregate stats (admins only) |

Any other text message is treated as content to analyze.

---

## Privacy policy summary

- **What we store:** Telegram user ID, language preference, per-message metadata (verdict, risk score, duration). That's it.
- **What we don't store:** the content of the messages users send for analysis.
- **What we send to Google:** only the message you submit, alongside the analysis prompt, to the Gemini API. See [Google's API privacy commitment](https://ai.google.dev/gemini-api/terms).
- **Open source:** every line is auditable in this repo.

---

## Development

### Run locally with auto-reload

```bash
pip install watchfiles
watchfiles 'python -m src.main' src
```

### Project layout

```
securelife-bot/
├── src/
│   ├── main.py                       # Entry point
│   ├── config.py                     # Env-driven config
│   ├── analyzer/
│   │   ├── gemini_client.py          # Gemini API wrapper
│   │   ├── heuristics.py             # Regex pre-checks
│   │   ├── phishing_detector.py      # Top-level coordinator
│   │   └── prompts.py                # LLM prompts
│   ├── bot/
│   │   ├── handlers.py               # Telegram handlers
│   │   └── keyboards.py              # Inline keyboards
│   ├── i18n/
│   │   ├── __init__.py               # Translation lookup
│   │   ├── en.py                     # English strings
│   │   └── uz.py                     # Uzbek strings
│   ├── storage/
│   │   └── db.py                     # SQLite (rate limit + lang)
│   └── utils/
│       ├── logging_config.py
│       └── url_extractor.py
├── deploy/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── securelife-bot.service
└── tests/
```

### Roadmap

- [ ] More heuristic coverage (look-alike domains, homograph detection)
- [ ] Optional Ollama backend for fully-local inference
- [ ] Inline mode (`@securelife_bot <text>`)
- [ ] Web preview screenshotting for URL analysis
- [ ] User feedback loop (👍/👎) to improve over time
- [ ] Public dataset of anonymized scam patterns (with consent)

---

## Contributing

Contributions are welcome. Please:

1. Open an issue describing the change first.
2. Fork the repo and work on a feature branch.
3. Run the bot locally against a test bot before submitting a PR.
4. Avoid storing message content anywhere new — privacy is a hard constraint.

---

## License

[MIT](./LICENSE) — use it, fork it, share it.

---

## Disclaimer

SecureLife is an *assistant*, not a guarantee. AI models can be wrong. When in doubt, do not click any link, do not share credentials, and contact the relevant organization through the official phone number printed on your card or their official website.

---

*Maintained by [@nodirsafarov](https://github.com/nodirsafarov). If this bot helped you, ⭐ the repo so others can find it.*
