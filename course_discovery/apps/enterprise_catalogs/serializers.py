"""
Serializers for enterprise_catalogs app.
"""
from urllib.parse import urlencode, urljoin

from rest_framework import serializers

from course_discovery.apps.course_metadata.models import CourseRun
from course_discovery.apps.course_metadata.utils import get_course_run_estimated_hours


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


class EnterpriseCatalogCourseSerializer(serializers.ModelSerializer):
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

    def _get_sku(self, obj):
        """Return SKU from the first available seat (internal use only)."""
        first_seat = obj.seats.first()
        return first_seat.sku if first_seat else None

    def get_enrollment_url(self, obj):
        """Return enrollment URL with coupon code and SKU."""
        coupon_code = self.context.get('coupon_code')
        partner = self.context.get('partner')
        sku = self._get_sku(obj)

        if not all([coupon_code, partner, getattr(partner, 'ecommerce_api_url', None), sku]):
            return None

        query_params = urlencode({'code': coupon_code, 'sku': sku})
        return f"{urljoin(partner.ecommerce_api_url, '/coupons/redeem/')}?{query_params}"
