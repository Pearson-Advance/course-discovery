"""
Views for enterprise_catalogs app.
"""
import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from course_discovery.apps.course_metadata.models import CourseRun
from course_discovery.apps.enterprise_catalogs.client import EnterpriseCatalogClient
from course_discovery.apps.enterprise_catalogs.exceptions import (
    EnterpriseCatalogAPIError, EnterpriseCatalogNotFoundError,
)
from course_discovery.apps.enterprise_catalogs.filters import EnterpriseCatalogCourseRunFilter
from course_discovery.apps.enterprise_catalogs.serializers import (
    EnterpriseCatalogCourseSerializer, EnterpriseCatalogQueryParamsSerializer,
)

logger = logging.getLogger(__name__)


class EnterpriseCatalogCoursesView(ListAPIView):
    """
    API view to list course runs from an Enterprise Catalog.

    Uses AllowAny permission since authentication is not required to access this endpoint.
    This allows the MFE to fetch catalog data without requiring user login.
    """

    permission_classes = (AllowAny,)
    throttle_classes = (AnonRateThrottle, UserRateThrottle,)
    serializer_class = EnterpriseCatalogCourseSerializer
    pagination_class = PageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = EnterpriseCatalogCourseRunFilter

    def get(self, request, *args, **kwargs):
        """Handle GET request with custom error handling."""
        query_params = EnterpriseCatalogQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        try:
            return super().get(request, *args, **kwargs)
        except EnterpriseCatalogNotFoundError as exc:
            return Response(
                {'error': exc.message},
                status=status.HTTP_404_NOT_FOUND,
            )
        except EnterpriseCatalogAPIError as exc:
            return Response(
                {'error': exc.message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_queryset(self):
        """Fetch courses from Discovery database based on Enterprise Catalog keys."""
        catalog_uuid = str(self.kwargs.get('catalog_uuid'))
        course_run_keys = EnterpriseCatalogClient(self.request.site.partner).get_course_run_keys(
            catalog_uuid,
        )

        queryset = CourseRun.objects.filter(
            key__in=course_run_keys,
            seats__sku__isnull=False,
        ).select_related(
            'course',
        ).prefetch_related(
            'course__topics',
            'seats',
        )

        excluded_keys = set(course_run_keys) - set(queryset.values_list('key', flat=True))
        if excluded_keys:
            logger.warning(
                'Course runs excluded from catalog %s due to missing SKU: %s.',
                catalog_uuid,
                excluded_keys,
            )

        return queryset

    def get_serializer_context(self):
        """Add validated coupon code and partner to serializer context."""
        context = super().get_serializer_context()
        context['coupon_code'] = self.request.query_params.get('coupon_code')
        context['partner'] = self.request.site.partner
        return context
