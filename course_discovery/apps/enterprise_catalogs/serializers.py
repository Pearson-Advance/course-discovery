"""
Serializers for enterprise_catalogs app.
"""
import json
import logging
from urllib.parse import urlencode

from rest_framework import serializers

from course_discovery.apps.course_metadata.models import CourseRun
from course_discovery.apps.course_metadata.utils import get_course_run_estimated_hours

logger = logging.getLogger(__name__)
COUPON_REDEEM_PATH = '/coupons/redeem/'


class EnterpriseCatalogQueryParamsSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Serializer to validate query parameters."""
    coupon_code = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=128,
        help_text='The coupon code to be used for enrollment.',
    )

    def validate_coupon_code(self, value):
        """
        Validate that coupon code contains only alphanumeric characters.

        Although CharField validates type and length, it allows spaces and special characters.
        Coupon codes for this integration must be strictly alphanumeric (no spaces or dashes),
        so this validation ensures invalid codes are rejected before reaching the enrollment service.
        """
        if not value.isalnum():
            raise serializers.ValidationError('Coupon code must contain only alphanumeric characters.')
        return value


class EnterpriseCatalogSerializerMixin:
    """Mixin with shared logic for enterprise catalog serializers."""

    def _get_sku(self, obj):
        """Return SKU from the professional seat."""
        seat = obj.seats.filter(type__slug='professional').first()
        return seat.sku if seat else None

    def get_enrollment_url(self, obj):
        """Return enrollment URL as a relative path with coupon code and SKU."""
        coupon_code = self.context.get('coupon_code')
        sku = self._get_sku(obj)

        if not all([coupon_code, sku]):
            return None

        query_params = urlencode({'code': coupon_code, 'sku': sku})
        return f"{COUPON_REDEEM_PATH}?{query_params}"


class EnterpriseCatalogCourseSerializer(EnterpriseCatalogSerializerMixin, serializers.ModelSerializer):
    """Serializer for CourseRun model in enterprise catalog context."""

    title = serializers.CharField(source='course.title')
    card_image_url = serializers.URLField(source='course.card_image_url')
    topics = serializers.SerializerMethodField()
    key = serializers.CharField()
    pacing_type = serializers.CharField()
    estimated_hours = serializers.SerializerMethodField()
    enrollment_url = serializers.SerializerMethodField()

    class Meta:
        model = CourseRun
        fields = (
            'title',
            'card_image_url',
            'topics',
            'key',
            'pacing_type',
            'estimated_hours',
            'enrollment_url',
        )

    def get_topics(self, obj):
        """Return list of topic names from the parent course."""
        return tuple(tag.name for tag in obj.course.topics.all())

    def get_estimated_hours(self, obj):
        """Return estimated hours to complete the course run."""
        return get_course_run_estimated_hours(obj)


class EnterpriseCatalogCourseDetailSerializer(EnterpriseCatalogSerializerMixin, serializers.ModelSerializer):
    """Serializer for individual CourseRun detail in enterprise catalog context."""

    _extra_description_cache = None
    title = serializers.CharField(source='course.title')
    overview = serializers.CharField(source='course.full_description', allow_null=True)
    outline = serializers.CharField(source='course.syllabus_raw', allow_null=True)
    prerequisites = serializers.CharField(source='course.prerequisites_raw', allow_null=True)
    learning_objectives = serializers.CharField(source='course.outcome', allow_null=True)
    vendor = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    included_materials = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    target_audience = serializers.SerializerMethodField()
    enrollment_url = serializers.SerializerMethodField()

    class Meta:
        model = CourseRun
        fields = (
            'title',
            'overview',
            'outline',
            'prerequisites',
            'learning_objectives',
            'vendor',
            'author',
            'included_materials',
            'duration',
            'target_audience',
            'enrollment_url',
        )

    def _get_extra_description_data(self, obj):
        """Parse extra_description JSON once per object and cache the result."""
        if self._extra_description_cache is not None:
            return self._extra_description_cache

        description = getattr(obj.course.extra_description, 'description', None)
        if not description:
            return {}

        try:
            self._extra_description_cache = json.loads(description)
        except (json.JSONDecodeError, TypeError):
            logger.exception(
                'Failed to parse extra_description JSON for course run %s.', obj,
            )
            self._extra_description_cache = {}

        return self._extra_description_cache

    def get_vendor(self, obj):
        """Return vendor name from extra_description JSON."""
        return self._get_extra_description_data(obj).get('vendor')

    def get_author(self, obj):
        """Return author from extra_description JSON."""
        return self._get_extra_description_data(obj).get('author')

    def get_included_materials(self, obj):
        """Return included materials list from extra_description JSON."""
        return self._get_extra_description_data(obj).get('included_materials')

    def get_duration(self, obj):
        """Return duration from extra_description JSON."""
        return self._get_extra_description_data(obj).get('duration')

    def get_target_audience(self, obj):
        """Return target audience from extra_description JSON."""
        return self._get_extra_description_data(obj).get('target_audience')

