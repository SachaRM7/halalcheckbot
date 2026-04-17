#!/usr/bin/env python3
"""HalalCheckBot — Flask web application."""

import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
_secret = os.getenv("SECRET_KEY")
if not _secret:
    import secrets
    _secret = secrets.token_hex(32)
    print("WARNING: SECRET_KEY not set — generated random key (sessions will reset on restart)")
app.secret_key = _secret

# Register blueprints
from web.routes import api, web

app.register_blueprint(api.api_bp)
app.register_blueprint(web.web_bp)


@app.route("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "halalcheckbot-web"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
