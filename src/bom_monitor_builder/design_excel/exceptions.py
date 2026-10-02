"""Exceptions for design Excel conversion."""

from __future__ import annotations


class DesignExcelError(Exception):
    """Base exception for design Excel conversion."""


class ProfileError(DesignExcelError):
    """Raised when a conversion profile is invalid."""


class ParseWorkbookError(DesignExcelError):
    """Raised when the input workbook cannot be parsed."""


class MappingError(DesignExcelError):
    """Raised when mapped output values cannot be produced."""


class TemplateWriteError(DesignExcelError):
    """Raised when the template workbook cannot be written."""


class ValidationError(DesignExcelError):
    """Raised when generated workbook validation fails."""
