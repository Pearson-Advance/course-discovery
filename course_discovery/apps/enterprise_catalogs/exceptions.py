"""
Custom exceptions for enterprise_catalogs app.
"""


class EnterpriseCatalogAPIError(Exception):
    """Base exception for Enterprise Catalog API errors."""

    message = 'Failed to fetch catalog content.'


class EnterpriseCatalogNotFoundError(EnterpriseCatalogAPIError):
    """Raised when catalog UUID is not found (404)."""

    message = 'Catalog not found.'
    status_code = 404
