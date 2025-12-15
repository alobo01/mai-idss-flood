"""Prediction subpackage for backend app

This file ensures the `prediction` directory is a Python package so
in-package relative imports (e.g. `from .prediction.inference_api import ...`)
work correctly when the `app` package is imported by the application.
"""

__all__ = ["inference_api"]
