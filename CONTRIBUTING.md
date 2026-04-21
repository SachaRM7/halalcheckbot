# Contributing to HalalCheckBot

JazakAllahu khayran for contributing to HalalCheckBot. This project helps the Muslim community verify ingredients and restaurants, so changes should stay transparent, practical, and easy to review.

## Ground rules

- Keep pull requests focused on one change.
- Prefer small, reviewable commits with clear messages.
- Preserve existing halal status labels: `halal`, `haram`, `mushbooh`, and `halal_if_no_alcohol`.
- Do not commit secrets, production tokens, or personal data.
- For halal/haram logic, include sources or a short justification in the PR description.

## Development setup

### Local Python setup

```bash
git clone https://github.com/SachaRM7/halalcheckbot.git
cd halalcheckbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python data/seed_data.py
```

Fill `.env` with the values you need:

- `TELEGRAM_BOT_TOKEN` for bot features
- `MINIMAX_API_KEY` for AI ingredient classification
- `SECRET_KEY` and `ADMIN_PASSWORD` for the web dashboard

Install Tesseract OCR if you plan to test image scanning:

```bash
# Ubuntu / Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### Docker setup

```bash
cp .env.example .env
docker-compose up --build
```

## Running the project

Start the Telegram bot:

```bash
python -m bot.main
```

Start the web dashboard:

```bash
python -m flask --app web.app run --port=5000
```

## Running tests

Run the test suite before opening a pull request:

```bash
pytest -q
```

If you changed database behavior, OCR, classifiers, or API routes, mention what you tested in the PR.

## Project layout

- `bot/` — Telegram bot logic, OCR, MiniMax classifier, keyboards, and database helpers
- `web/` — Flask app, HTML templates, and API routes
- `data/` — SQLite seed script and database files
- `tests/` — automated tests

## Branch and commit guidance

Suggested branch prefixes:

- `feat/` for features
- `fix/` for bug fixes
- `docs/` for documentation
- `chore/` for maintenance

Use clear commit messages, for example:

```text
docs: add contribution guidelines
fix: handle missing OCR dependency gracefully
feat: add restaurant moderation endpoint
```

## Pull request checklist

Before submitting a PR, make sure you:

- Updated documentation when behavior changed
- Ran `pytest -q`
- Kept the change scoped and readable
- Added screenshots or API examples when UI or API behavior changed
- Explained any halal classification or data-source decisions

## Reporting issues

When opening an issue, include:

- What you expected to happen
- What actually happened
- Steps to reproduce
- Logs, screenshots, or sample payloads if helpful
- Environment details (OS, Python version, Docker/local)

## Security

If you discover a security issue or exposed credential, do not open a public issue with the secret included. Rotate the secret immediately and share only sanitized details.

May Allah put barakah in your contribution.
