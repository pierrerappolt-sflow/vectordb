"""Vector search service that runs as a separate server."""

from .api import create_search_app
from .main import run_search_service

__all__ = ["create_search_app", "run_search_service"]
