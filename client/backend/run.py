"""
Entry point for the Scrim.GG client backend.
Replaces bootstrap.py
"""
from app import create_app
from app import settings

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG
    )

