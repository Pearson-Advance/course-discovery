"""
Strategy pattern for parsing Enterprise Catalog API responses.

The Enterprise Catalog API can return different content types based on the
catalog's content filter configuration. This module provides strategies to
extract course run keys from different response formats.
"""
from abc import ABC, abstractmethod


class ContentParserStrategy(ABC):
    """Abstract base class for content parsing strategies."""

    content_type = None

    @staticmethod
    @abstractmethod
    def extract_course_run_keys(results):
        """Extract course run keys from the API results."""

    @classmethod
    def can_handle(cls, results):
        """Determine if this strategy can handle the given results."""
        if not results:
            return False
        return results[0].get('content_type') == cls.content_type


class CourseRunContentStrategy(ContentParserStrategy):
    """Strategy for content_type: courserun."""

    content_type = 'courserun'

    @staticmethod
    def extract_course_run_keys(results):
        return tuple(
            item.get('key')
            for item in results
            if item.get('key')
        )


class CourseContentStrategy(ContentParserStrategy):
    """Strategy for content_type: course."""

    content_type = 'course'

    @staticmethod
    def extract_course_run_keys(results):
        return tuple(
            run.get('key')
            for course in results
            for run in course.get('course_runs', [])
            if run.get('key')
        )


class ContentParserStrategyFactory:
    """Factory for selecting the appropriate content parser strategy."""

    _strategies = (
        CourseRunContentStrategy,
        CourseContentStrategy,
    )

    @staticmethod
    def get_strategy(results):
        for strategy_class in ContentParserStrategyFactory._strategies:
            if strategy_class.can_handle(results):
                return strategy_class

        content_type = results[0].get('content_type', 'unknown') if results else 'unknown'
        raise ValueError(f'No strategy found for content_type: {content_type}.')
