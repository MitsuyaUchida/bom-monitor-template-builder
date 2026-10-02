"""Exceptions for build orchestration."""

from __future__ import annotations


class BuildError(Exception):
    """Base exception for build workflow errors."""


class ProfileDetectionError(BuildError):
    """Raised when profile auto-detection fails."""
