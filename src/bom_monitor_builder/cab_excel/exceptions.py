"""Exceptions for BOM CAB Excel generation."""


class CabExcelError(Exception):
    """Base exception for CAB to Excel processing."""


class InputError(CabExcelError):
    """Raised when an input path or argument is invalid."""


class ExtractionError(CabExcelError):
    """Raised when CAB extraction fails."""


class ParseError(CabExcelError):
    """Raised when manifest or XML parsing fails."""


class ExcelWriteError(CabExcelError):
    """Raised when workbook creation or saving fails."""
