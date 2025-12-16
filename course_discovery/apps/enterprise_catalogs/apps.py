"""
Configuration for the Enterprise Catalogs application.
"""
from django.apps import AppConfig


class EnterpriseCatalogsConfig(AppConfig):
    """
    Django application configuration for Enterprise Catalogs.

    This application retrieves course data associated with an Enterprise customer catalog.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'enterprise_catalogs'
