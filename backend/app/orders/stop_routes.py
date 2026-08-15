"""Backward-compatible re-export of stop routes."""

from app.orders.routes import stops_router as router

__all__ = ["router"]
