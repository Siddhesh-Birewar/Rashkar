"""
CropNet AI API v1 Router Specification.
Re-exports api_router from router.py for compatibility.
"""
from cropnet.services.api.app.api.v1.router import api_router

__all__ = ["api_router"]
