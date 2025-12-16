"""
URL configuration for enterprise_catalogs app.
"""

from django.urls import path

from course_discovery.apps.enterprise_catalogs import views

app_name = 'enterprise_catalogs'

urlpatterns = [
    path(
        '<uuid:catalog_uuid>/courses/',
        views.EnterpriseCatalogCoursesView.as_view(),
        name='enterprise-catalog-courses',
    ),
]
