"""
Quart application factory.
Creates app, registers blueprints, sets up lifecycle.
"""
import asyncio
import contextlib
from quart import Quart
from quart_cors import cors

from .sockets.manager import ConnectionManager
from .services.valorant import ValorantService
from .sockets.routes import ws_bp
from .routes.health import health_bp
from . import settings

# Import all handlers to register them
from .sockets import handlers

def create_app() -> Quart:
    """Create and configure the Quart application."""
    app = Quart(__name__)
    
    # Configure CORS
    app = cors(
        app,
        allow_origin=settings.CORS_ORIGIN,
        allow_methods=["POST", "GET", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        allow_credentials=True
    )
    
    # Initialize services (store as app attributes)
    app.conn_mgr = ConnectionManager()
    app.valorant = ValorantService()
    
    # Register blueprints
    app.register_blueprint(ws_bp)
    app.register_blueprint(health_bp)
    
    @app.before_serving
    async def startup():
        """Run startup tasks."""
        print("=" * 60)
        print("Starting Scrim.GG Client Service")
        print("=" * 60)
        print(f"WebSocket server: ws://{settings.HOST}:{settings.PORT}/ws")
        print(f"Health check: http://{settings.HOST}:{settings.PORT}/health")
        print("Ready to connect to Valorant")
        print("=" * 60)
        
        # Start heartbeat
        app.heartbeat_task = asyncio.create_task(
            app.conn_mgr.start_heartbeat(app.valorant)
        )
    
    @app.after_serving
    async def shutdown():
        """Run shutdown tasks."""
        print("Shutting down...")
        
        # Stop heartbeat
        if hasattr(app, 'heartbeat_task') and app.heartbeat_task:
            app.heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await app.heartbeat_task
        
        # Close all connections
        await app.conn_mgr.close_all()
        
        print("Cleanup complete")
    
    return app
