from __future__ import annotations


class SalesAnalyticsError(Exception):
    """Base exception for the sales analytics domain."""


class DataQualityError(SalesAnalyticsError):
    """Raised when the dataset cannot be used for analysis."""
