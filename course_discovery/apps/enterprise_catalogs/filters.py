"""
Filters for enterprise_catalogs app.
"""
from django_filters import rest_framework as filters

from course_discovery.apps.course_metadata.models import CourseRun


class EnterpriseCatalogCourseRunFilter(filters.FilterSet):
    """FilterSet for Enterprise Catalog course runs."""

    search = filters.CharFilter(field_name='course__title', lookup_expr='icontains')
    topics = filters.BaseInFilter(field_name='course__topics__name', distinct=True)

    class Meta:
        model = CourseRun
        fields = ('search', 'topics',)
