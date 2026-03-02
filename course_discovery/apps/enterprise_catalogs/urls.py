"""
URL configuration for enterprise_catalogs app.
"""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from course_discovery.apps.enterprise_catalogs.views import EnterpriseCatalogCoursesViewSet

app_name = 'enterprise_catalogs'

router = SimpleRouter()
router.register('courses', EnterpriseCatalogCoursesViewSet, basename='enterprise-catalog-courses')

urlpatterns = [
    path('<uuid:catalog_uuid>/', include(router.urls)),
]
