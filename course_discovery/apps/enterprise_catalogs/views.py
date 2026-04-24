"""
Views for enterprise_catalogs app.
"""
import logging

from django_filters.rest_framework import DjangoFilterBackend
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from course_discovery.apps.api.pagination import PageNumberPagination
from course_discovery.apps.course_metadata.models import CourseRun
from course_discovery.apps.enterprise_catalogs.client import EnterpriseCatalogClient
from course_discovery.apps.enterprise_catalogs.exceptions import (
    EnterpriseCatalogAPIError, EnterpriseCatalogCourseNotFoundError, EnterpriseCatalogNotFoundError,
)
from course_discovery.apps.enterprise_catalogs.filters import EnterpriseCatalogCourseRunFilter
from course_discovery.apps.enterprise_catalogs.serializers import (
    EnterpriseCatalogCourseDetailSerializer, EnterpriseCatalogCourseSerializer, EnterpriseCatalogQueryParamsSerializer,
)

logger = logging.getLogger(__name__)


class EnterpriseCatalogCoursesViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet,
):
    """
    ViewSet to list and retrieve course runs from an Enterprise Catalog.

    - LIST: GET /enterprise_catalogs/{catalog_uuid}/courses/
    - RETRIEVE: GET /enterprise_catalogs/{catalog_uuid}/courses/{course_run_key}/

    Uses AllowAny permission since authentication is not required to access this endpoint.
    This allows the MFE to fetch catalog data without requiring user login.
    """

    permission_classes = (AllowAny,)
    throttle_classes = (AnonRateThrottle, UserRateThrottle,)
    serializer_class = EnterpriseCatalogCourseSerializer
    pagination_class = PageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = EnterpriseCatalogCourseRunFilter
    lookup_url_kwarg = 'course_run_key'

    def get_serializer_class(self):
        """Return detail serializer for retrieve, list serializer otherwise."""
        if self.action == 'retrieve':
            return EnterpriseCatalogCourseDetailSerializer
        return EnterpriseCatalogCourseSerializer

    def initial(self, request, *args, **kwargs):
        """Validate query params before any action."""
        super().initial(request, *args, **kwargs)
        query_params = EnterpriseCatalogQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)

    def get_queryset(self):
        """Fetch courses from Discovery database based on Enterprise Catalog keys."""
        catalog_uuid = str(self.kwargs.get('catalog_uuid'))
        course_run_keys = EnterpriseCatalogClient(self.request.site.partner).get_course_run_keys(
            catalog_uuid,
        )

        queryset = CourseRun.objects.filter(
            key__in=course_run_keys,
            seats__sku__isnull=False,
            seats__type__slug='professional',
        ).select_related(
            'course',
            'course__extra_description',
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

    def get_object(self):
        """Get single course run, validating membership in catalog."""
        catalog_uuid = str(self.kwargs.get('catalog_uuid'))
        course_run_key = self.kwargs.get('course_run_key')

        if not self._is_valid_course_run_key(course_run_key):
            logger.warning('Invalid course_run_key format received: %s.', course_run_key)
            raise EnterpriseCatalogCourseNotFoundError()

        catalog_keys = EnterpriseCatalogClient(self.request.site.partner).get_course_run_keys(catalog_uuid)
        if course_run_key not in catalog_keys:
            raise EnterpriseCatalogCourseNotFoundError()

        try:
            return CourseRun.objects.select_related(
                'course',
                'course__extra_description',
            ).prefetch_related(
                'seats',
            ).get(key=course_run_key, seats__sku__isnull=False, seats__type__slug='professional')
        except CourseRun.DoesNotExist:
            raise EnterpriseCatalogCourseNotFoundError()

    def get_serializer_context(self):
        """Add validated coupon code and partner to serializer context."""
        context = super().get_serializer_context()
        context['coupon_code'] = self.request.query_params.get('coupon_code')
        context['partner'] = self.request.site.partner
        return context

    def handle_exception(self, exc):
        """Handle catalog-specific exceptions."""
        if isinstance(exc, (EnterpriseCatalogNotFoundError, EnterpriseCatalogCourseNotFoundError)):
            return Response(
                {'error': exc.message},
                status=status.HTTP_404_NOT_FOUND,
            )
        if isinstance(exc, EnterpriseCatalogAPIError):
            return Response(
                {'error': exc.message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return super().handle_exception(exc)

    @staticmethod
    def _is_valid_course_run_key(course_run_key):
        """Return True if course_run_key is a valid CourseKey string."""
        try:
            CourseKey.from_string(course_run_key)
            return True
        except InvalidKeyError:
            return False
