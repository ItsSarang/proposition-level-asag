"""
Flask Application alias for ASAG Backend.

Allows running via either:
    python backend/main.py
or:
    python backend/app.py
"""
import os
from backend.main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
