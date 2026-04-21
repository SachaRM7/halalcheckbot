# Contributing to HalalCheckBot

Thank you for your interest in contributing to HalalCheckBot! This is an open-source, community-driven project serving the Muslim community worldwide by providing halal ingredient and restaurant verification. We welcome contributions of all kinds — bug fixes, new features, documentation improvements, and more.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Local Development Setup](#local-development-setup)
   - [Running Tests](#running-tests)
3. [How to Contribute](#how-to-contribute)
   - [Reporting Bugs](#reporting-bugs)
   - [Suggesting Features](#suggesting-features)
   - [Contributing Code](#contributing-code)
4. [Development Guidelines](#development-guidelines)
   - [Coding Standards](#coding-standards)
   - [Python Style Guide](#python-style-guide)
   - [Git Commit Messages](#git-commit-messages)
5. [Project Structure](#project-structure)
6. [API & Database Guidelines](#api--database-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [Halal Verification Standards](#halal-verification-standards)
9. [License](#license)

---

## Code of Conduct

By participating in this project, you agree to maintain a respectful, inclusive, and harassment-free environment for everyone. We do not tolerate discrimination, offensive language, or disrespectful behavior toward any individual or group, particularly regarding religious beliefs and practices.

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Telegram Bot Token ([get one from @BotFather](https://t.me/BotFather))
- Optional: MiniMax API Key for AI-powered ingredient classification
- Tesseract OCR (system package)

### Local Development Setup

1. **Fork the repository**

   Click the "Fork" button on GitHub, then clone your fork:

   ```bash
   git clone https://github.com/<your-username>/halalcheckbot.git
   cd halalcheckbot
   ```

2. **Add the upstream remote**

   ```bash
   git remote add upstream https://github.com/oummah/halalcheckbot.git
   ```

3. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Install Tesseract OCR**

   ```bash
   # Linux
   sudo apt-get install tesseract-ocr

   # macOS
   brew install tesseract
   ```

6. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env and fill in your tokens
   ```

7. **Seed the database**

   ```bash
   python data/seed_data.py
   ```

8. **Run the bot**

   ```bash
   python -m bot.main
   ```

9. **Run the web dashboard (in a separate terminal)**

   ```bash
   python -m flask --app web.app run --port=5000
   ```

### Running Tests

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ -v --cov=bot --cov=web
```

---

## How to Contribute

### Reporting Bugs

Before submitting a bug report:

1. **Check existing issues** to avoid duplicates.
2. **Use the bug report template** when opening a new issue.
3. Include:
   - Python version, Telegram Bot API version
   - Steps to reproduce the bug
   - Expected vs. actual behavior
   - Any relevant logs or screenshots
   - Your `.env` configuration (mask sensitive values)

### Suggesting Features

We welcome feature suggestions, especially:

- New verification categories (e.g., cosmetics, pharmaceuticals)
- Additional language support
- Improved OCR accuracy methods
- Community voting / trust score enhancements
- Integration with external halal certification databases

Open a **Feature Request** issue with the `enhancement` label and describe:
- The problem you are trying to solve
- How you envision the solution
- Any alternatives you considered

### Contributing Code

1. **Pick an issue** from the [issue tracker](../../issues) or fix a bug you found.
2. **Comment on the issue** to let others know you're working on it.
3. **Follow the coding standards** outlined below.
4. **Write tests** for your changes.
5. **Submit a Pull Request** (see [Pull Request Process](#pull-request-process)).

---

## Development Guidelines

### Coding Standards

- **Python 3.11+**: Use modern Python syntax and features (type hints, dataclasses, match statements where appropriate).
- **No breaking changes**: Do not introduce breaking changes to the existing API or bot commands without discussion.
- **Small, focused changes**: Keep PRs focused on a single issue or feature. Multiple concerns = multiple PRs.
- **Backward compatibility**: Preserve existing database schema and API contracts when possible.
- **Security**: Never commit secrets, API keys, or tokens. Use environment variables exclusively.

### Python Style Guide

- Follow **PEP 8** with a maximum line length of **100 characters**.
- Use **type hints** for all function parameters and return values.
- Use **docstrings** for all public modules, classes, and functions.
- Import order: standard library → third-party → local application (enforced by `isort`).

Example:

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class Ingredient:
    """Represents a halal/haram ingredient entry."""
    name: str
    status: str  # 'halal', 'haram', 'mushbooh', 'halal_if_no_alcohol'
    scholar_notes: Optional[str] = None
    source: Optional[str] = None


def check_ingredient(name: str, db_path: str = "data/halalcheck.db") -> Optional[Ingredient]:
    """Look up an ingredient by name in the database.

    Args:
        name: The ingredient name to search for.
        db_path: Path to the SQLite database file.

    Returns:
        An Ingredient object if found, otherwise None.

    Raises:
        ValueError: If the ingredient name is empty.
    """
    if not name or not name.strip():
        raise ValueError("Ingredient name cannot be empty")
    ...
```

### Git Commit Messages

Use clear, descriptive commit messages:

- **Subject line**: 72 characters max, imperative mood ("Add feature", not "Added feature")
- **Body**: Explain *what* and *why*, not *how*. Reference issues with `Fixes #123` or `Closes #456`.

Good examples:
```
Add OCR support for ingredient label scanning

Implements /scan command using Tesseract to extract ingredient
lists from product photos. Closes #12.
```

```
Fix database race condition in concurrent vote handling

Uses sqlite3 connection per request instead of sharing a global
connection. Fixes #34.
```

Bad examples:
```
fix stuff
WIP
asdf
```

---

## Project Structure

```
halalcheckbot/
├── bot/                    # Telegram bot module
│   ├── __init__.py
│   ├── main.py             # Bot entry point, event loop
│   ├── handlers.py          # Telegram command & message handlers
│   ├── database.py          # SQLite CRUD operations
│   ├── classifier.py        # MiniMax AI classification logic
│   ├── ocr_processor.py     # Tesseract OCR image processing
│   └── keyboards.py         # Inline keyboard layouts
├── web/                    # Flask web dashboard
│   ├── __init__.py
│   ├── app.py               # Flask application factory
│   ├── routes/
│   │   ├── api.py           # REST API endpoints
│   │   └── web.py           # Web page routes
│   └── templates/           # Jinja2 HTML templates
│       ├── base.html
│       ├── index.html
│       └── dashboard.html
├── data/                   # Data layer
│   ├── seed_data.py         # Database seeder script
│   └── halalcheck.db        # SQLite database (gitignored)
├── tests/                  # Test suite
│   └── test_halalcheckbot.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── CONTRIBUTING.md
└── README.md
```

---

## API & Database Guidelines

### REST API

- All endpoints return **JSON**.
- Follow the existing response format: `{"status": "ok"|"error", "data": ...}`.
- Input validation must be done before database operations.
- Use appropriate HTTP status codes (200, 400, 404, 500).

### Database (SQLite)

- Use parameterized queries to prevent SQL injection.
- The database file (`halalcheck.db`) is gitignored — do not commit it.
- Schema changes require a migration strategy. Document any ALTER TABLE or CREATE TABLE changes in the PR description.
- All user-facing text fields should be UTF-8.

---

## Pull Request Process

### PR Checklist

Before submitting a PR, verify:

- [ ] Your branch is based on the latest `master` / `main` from upstream.
- [ ] Code follows the [coding standards](#coding-standards) above.
- [ ] Type hints are present on all new functions and methods.
- [ ] New functions/classes have docstrings.
- [ ] New features have corresponding tests.
- [ ] Existing tests still pass (`pytest tests/ -v`).
- [ ] No secrets or tokens are committed (check `git diff` before pushing).
- [ ] Commit messages follow the [commit message guidelines](#git-commit-messages).
- [ ] Documentation (README, docstrings) is updated if behavior changes.

### Submission

1. **Push your branch**:

   ```bash
   git push origin contrib/adding-contributing
   ```

2. **Open a Pull Request** on GitHub against the `master` branch.

3. **Fill in the PR template**:
   - **Title**: Clear, concise summary of the change.
   - **Description**: What does this PR do? Why? Link to the relevant issue.
   - **Screenshots/Logs**: If applicable, include proof of working changes.
   - **Checklist**: Confirm all items in the PR checklist above.

4. **Respond to review feedback** — the maintainer may request changes before merging.

### Review Criteria

PRs are reviewed based on:

- Correctness (does it work as intended?)
- Code quality (readability, maintainability)
- Test coverage
- Alignment with the project's goals (serving the Muslim community with accurate halal verification)
- No regressions to existing functionality

---

## Halal Verification Standards

This project deals with matters of Islamic dietary law. Contributors must follow these standards:

- **Cite sources**: All halal/haram determinations must reference recognized Islamic scholarly sources (Quran, Sahih Hadith, or established fatwa councils like DOJ, IFANCA, HMC).
- **Use the correct status**: Only one of four statuses is valid:
  | Status | Meaning |
  |--------|---------|
  | `halal` | Clearly permissible |
  | `haram` | Clearly forbidden |
  | `mushbooh` | Doubtful — requires further scholarly verification |
  | `halal_if_no_alcohol` | Permissible only if no alcohol is present |
- **Flag uncertain entries**: If you are unsure about a substance's status, mark it as `mushbooh` rather than guessing.
- **Community voting**: Trust scores help surface the most reliable entries, but they do not replace scholarly consensus.
- **Dispute resolution**: For contested entries, a note should be added noting the disagreement among scholars, and the status should be set to `mushbooh` until resolved.

> **Disclaimer**: This bot provides informational assistance only. Always verify critical halal/haram decisions with a qualified Islamic scholar.

---

## License

By contributing to HalalCheckBot, you agree that your contributions will be licensed under the MIT License.

---

**🕌 JazakAllahu khairan for contributing to HalalCheckBot!**
