import logging

from openai import OpenAI

logger = logging.getLogger(__name__)

_client = None


def get_openai_client():
    global _client
    if _client is None:
        _client = OpenAI(timeout=25.0, max_retries=1)
    return _client
