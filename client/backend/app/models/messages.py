"""
Pydantic models for WebSocket message validation.
"""
from pydantic import BaseModel, Field
from typing import Any, Optional

class Envelope(BaseModel):
    """Standard message envelope for all WebSocket communication."""
    event: str = Field(..., description="Event type/name")
    payload: Optional[Any] = Field(default=None, description="Event payload")

class ErrorResponse(BaseModel):
    """Standard error response."""
    message: str
    code: Optional[str] = None

class StatusUpdate(BaseModel):
    """Status update payload."""
    backend_connected: bool
    valorant: dict
    authenticated: bool

