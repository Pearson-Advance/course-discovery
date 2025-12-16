"""
Client for Enterprise Catalog API.
"""
import logging
from urllib.parse import urljoin

from django.conf import settings
from requests.exceptions import RequestException

from course_discovery.apps.enterprise_catalogs.exceptions import (
    EnterpriseCatalogAPIError, EnterpriseCatalogNotFoundError,
)
from course_discovery.apps.enterprise_catalogs.strategies import ContentParserStrategyFactory

logger = logging.getLogger(__name__)


class EnterpriseCatalogClient:
    """Client for Enterprise Catalog API."""

    CATALOG_ENDPOINT_TEMPLATE = '/api/v1/enterprise-catalogs/{uuid}/get_content_metadata/'
    PAGE_SIZE = 100
    REQUEST_TIMEOUT = 30

    def __init__(self, partner):
        self.oauth_api_client = partner.oauth_api_client

    def get_course_run_keys(self, catalog_uuid):
        """Fetch course run keys for a catalog from Enterprise Catalog service."""
        base_url = getattr(settings, 'ENTERPRISE_CATALOG_SERVICE_URL', '').rstrip('/')
        url = urljoin(base_url, self.CATALOG_ENDPOINT_TEMPLATE.format(uuid=catalog_uuid))
        params = {'page_size': self.PAGE_SIZE}

        first_page = self._make_request(url, params)
        all_results = list(first_page.get('results', []))
        total_count = first_page.get('count', 0)
        # Ceiling division to determine total pages from total count and page size.
        total_pages = (total_count + self.PAGE_SIZE - 1) // self.PAGE_SIZE if total_count else 1

        for page in range(2, total_pages + 1):
            params['page'] = page
            all_results.extend(self._make_request(url, params).get('results', []))

        if not all_results:
            logger.info('No results found for catalog %s.', catalog_uuid)
            return ()

        strategy = ContentParserStrategyFactory.get_strategy(all_results)
        course_run_keys = strategy.extract_course_run_keys(all_results)

        logger.info('Retrieved %s course runs for catalog %s.', len(course_run_keys), catalog_uuid)

        return course_run_keys

    def _make_request(self, url, params):
        """Make a request to the Enterprise Catalog API with error handling."""
        try:
            response = self.oauth_api_client.get(url, params=params, timeout=self.REQUEST_TIMEOUT)
            if response.status_code == 404:
                raise EnterpriseCatalogNotFoundError()
            if response.status_code >= 400:
                raise EnterpriseCatalogAPIError()
        except RequestException as exc:
            raise EnterpriseCatalogAPIError() from exc

        return response.json()
