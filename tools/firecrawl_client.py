"""Firecrawl REST API client - deterministic wrapper for scraping and search."""

import time
import requests
from utils import get_env


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {get_env('FIRECRAWL_API_KEY')}",
        "Content-Type": "application/json",
    }


def scrape(url: str, timeout: int = 30) -> str:
    """Scrape a single URL and return its markdown content."""
    resp = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers=_headers(),
        json={"url": url, "formats": ["markdown"]},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"Firecrawl scrape failed: {data}")
    return data.get("data", {}).get("markdown", "")


def search(query: str, limit: int = 5, timeout: int = 30) -> list[dict]:
    """Search the web and return a list of {url, title, description, markdown} dicts."""
    resp = requests.post(
        "https://api.firecrawl.dev/v1/search",
        headers=_headers(),
        json={"query": query, "limit": limit, "scrapeOptions": {"formats": ["markdown"]}},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"Firecrawl search failed: {data}")
    return data.get("data", [])


def search_text(query: str, limit: int = 5, max_chars_per_result: int = 2000) -> str:
    """Search and return concatenated text summary suitable for LLM context."""
    results = search(query, limit=limit)
    parts = []
    for r in results:
        title = r.get("title", r.get("url", ""))
        url = r.get("url", "")
        content = (r.get("markdown") or r.get("description") or "")[:max_chars_per_result]
        parts.append(f"### {title}\nURL: {url}\n{content}")
    return "\n\n".join(parts)
