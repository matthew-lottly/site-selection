"""Base class for the pipeline's read-only, key-free HTTP data-source clients."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

from .paths import RAW


class ApiClient:
    """Common request/cache behavior shared by every data-source client.

    Subclasses set ``BASE_URL`` (and optionally ``HEADERS``) and expose
    domain-specific ``fetch_*`` methods that call :meth:`get_json` (GET) or
    :meth:`post_json` (POST, used by the Overpass API).
    """

    BASE_URL: str = ""
    HEADERS: dict[str, str] = {"User-Agent": "curl/8.7.1", "Accept": "*/*"}
    DEFAULT_TIMEOUT = 30

    def __init__(self, cache_dir: Path = RAW) -> None:
        self.cache_dir = cache_dir

    def _cache_path(self, cache_name: str) -> Path:
        return self.cache_dir / f"{cache_name}.json"

    def _request(
        self,
        url: str,
        params: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
        verify: bool = True,
    ) -> dict:
        resp = requests.get(
            url,
            params=params,
            headers=headers or self.HEADERS,
            timeout=timeout or self.DEFAULT_TIMEOUT,
            verify=verify,
        )
        resp.raise_for_status()
        return resp.json()

    def get_json(
        self,
        url: str,
        params: dict[str, Any],
        cache_name: str,
        *,
        verify: bool = True,
        timeout: int | None = None,
    ) -> dict:
        """GET with disk caching so repeated pipeline runs don't hammer public APIs."""
        cache_path = self._cache_path(cache_name)
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))

        data = self._request(url, params, timeout=timeout, verify=verify)
        cache_path.write_text(json.dumps(data), encoding="utf-8")
        time.sleep(0.2)
        return data

    def post_json(
        self,
        url: str,
        data: dict[str, Any],
        cache_name: str,
        *,
        timeout: int | None = None,
    ) -> dict:
        """POST with disk caching (used by the Overpass query API)."""
        cache_path = self._cache_path(cache_name)
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))

        resp = requests.post(url, data=data, headers=self.HEADERS, timeout=timeout or self.DEFAULT_TIMEOUT)
        resp.raise_for_status()
        result = resp.json()
        cache_path.write_text(json.dumps(result), encoding="utf-8")
        time.sleep(0.2)
        return result
