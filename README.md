# HalalCheckBot

**Open-source, community-driven halal ingredient & restaurant verification for the Oummah.**

An Islamic fintech foundation enabling Muslims worldwide to verify if food products, ingredients, or restaurants are halal (permissible) according to Islamic guidelines.

---

## Features

- **Instant Ingredient Verification** — Check single or multiple ingredients with halal/haram status and scholarly explanations
- **OCR Scanning** — Upload a photo of a product's ingredient list for automatic extraction and verification
- **Halal Restaurant Search** — Find community-verified halal restaurants by city
- **Community Contributions** — Submit and vote on entries, building transparent trust scores
- **AI Classification** — MiniMax-powered classification for unknown ingredients
- **Web Dashboard** — REST API + searchable web interface

---

## Quick Start

### Prerequisites

- Python 3.11+
- Telegram Bot Token ([from @BotFather](https://t.me/BotFather))
- MiniMax API Key (optional, for AI classification)

### Installation

```bash
# Clone the repository
git clone https://github.com/oummah/halalcheckbot.git
cd halalcheckbot

# Install Python dependencies
pip install -r requirements.txt

# Install Tesseract OCR (Linux)
sudo apt-get install tesseract-ocr

# Install Tesseract OCR (macOS)
brew install tesseract

# Copy and configure environment variables
cp .env.example .env
nano .env  # Fill in your tokens

# Seed the database with ~500 common ingredients
python data/seed_data.py

# Start the Telegram bot
python -m bot.main

# In another terminal, start the web dashboard
python -m flask --app web.app run --port=5000
```

### Docker

```bash
cp .env.example .env
# Edit .env with your tokens
docker-compose up --build
```

---

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + quick tour |
| `/check <ingredient>` | Verify an ingredient (or comma-separated list) |
| `/scan` | Upload a photo for OCR ingredient scanning |
| `/restaurant <city>` | Search halal restaurants in a city |
| `/restaurant add` | Add a new restaurant (interactive) |
| `/vote <entry_id> <up\|down>` | Vote on community entries |
| `/stats` | View database statistics |
| `/about` | About HalalCheckBot |
| `/donate` | Support the project |
| `/feedback <message>` | Open a prefilled feedback form for maintainers |

---

## Ingredient Statuses

| Status | Meaning |
|--------|---------|
| `halal` | Permissible — clearly allowed |
| `haram` | Forbidden — clearly not allowed |
| `mushbooh` | Doubtful — requires further verification |
| `halal_if_no_alcohol` | Permissible only if alcohol is absent |

---

## API Reference

### Search Ingredients
```
GET /api/search?q=<ingredient_name>
```

### Search Restaurants
```
GET /api/restaurants?city=<city_name>
```

### Get Statistics
```
GET /api/stats
```

### Submit Entry
```
POST /api/contribute
{
  "type": "ingredient" | "restaurant",
  "name": "...",
  ...
}
```

### Vote
```
POST /api/vote
{
  "entry_type": "ingredient" | "restaurant",
  "entry_id": 123,
  "vote": 1 | -1,
  "tg_id": "user123"
}
```

---

## Directory Structure

```
halalcheckbot/
├── bot/
│   ├── __init__.py
│   ├── main.py          # Bot entry point
│   ├── handlers.py      # Telegram command handlers
│   ├── cmd_feedback.py  # /feedback command handler
│   ├── database.py      # SQLite operations
│   ├── classifier.py     # MiniMax AI classification
│   ├── ocr_processor.py # Image OCR processing
│   └── keyboards.py     # Inline keyboards
├── web/
│   ├── __init__.py
│   ├── app.py           # Flask app
│   ├── routes/
│   │   ├── api.py       # REST API
│   │   └── web.py       # Web pages
│   └── templates/
│       ├── base.html
│       ├── index.html
│       └── dashboard.html
├── data/
│   ├── seed_data.py     # Pre-seed 500 ingredients
│   └── halalcheck.db    # SQLite database (created on first run)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## Legal Disclaimer

**HalalCheckBot provides informational assistance only.** Always verify critical halal/haram decisions with qualified Islamic scholars. The developers accept no liability for food choices made based on this bot's output.

---

## Contributing

Contributions welcome! Please read the contribution guidelines and submit PRs to [github.com/oummah/halalcheckbot](https://github.com/oummah/halalcheckbot).

---

## License

MIT License — Open-source for the Oummah.

---

**🕌 Built with ❤️ for the Muslim community worldwide.**
