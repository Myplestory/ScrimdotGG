"""
Health check endpoint for Electron readiness detection.
"""
from quart import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

@health_bp.get("/health")
async def health():
    """Simple health check - returns 200 OK when server is ready."""
    return jsonify({"ok": True, "status": "healthy"})

