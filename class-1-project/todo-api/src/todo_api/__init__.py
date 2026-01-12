"""Todo API - Production-grade REST API with JWT authentication.

Main exports for backward compatibility.
All application logic has been moved to main.py for better organization.
"""

from .main import create_app, main

__all__ = ["create_app", "main"]

