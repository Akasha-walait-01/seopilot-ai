# This file is our SERP (Search Engine Results Page) provider abstraction
# Spec section 33: keep provider integrations replaceable
# Right now only a Mock Provider is implemented, since no paid SERP API
# key is configured. When a real provider (SerpApi, DataForSEO, etc) is
# added, it should implement the same search() interface.

from abc import ABC, abstractmethod


class SERPProvider(ABC):
    @abstractmethod
    def search(self, keyword: str, country: str = "us", language: str = "en") -> dict:
        """Return SERP data for a keyword, or a 'not configured' response."""
        pass


class MockSERPProvider(SERPProvider):
    # returns a clear "not configured" response instead of fake ranking data
    def search(self, keyword: str, country: str = "us", language: str = "en") -> dict:
        return {
            "configured": False,
            "keyword": keyword,
            "message": "SERP provider not configured. Add a real SERP API key to enable live ranking data.",
            "results": [],
        }


def get_serp_provider() -> SERPProvider:
    # this is the single place to swap in a real provider later
    # example: return SerpApiProvider(api_key=settings.serp_api_key)
    return MockSERPProvider()