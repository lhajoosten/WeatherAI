"""
Entry point for running management commands.

Usage:
    python -m app.manage seed-data --days 7 --locations all
"""

from app.manage import app

if __name__ == "__main__":
    app()
