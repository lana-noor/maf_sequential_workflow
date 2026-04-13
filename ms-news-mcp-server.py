"""
Microsoft News RSS MCP Server
==============================

A FastMCP server that fetches Microsoft-published news from official RSS feeds
and serves them as structured article data to the MicrosoftSourceAgent.

RSS Feeds:
  - Azure Blog:        https://azure.microsoft.com/en-us/blog/feed/
  - Microsoft Blog:    https://blogs.microsoft.com/feed/
  - Tech Community:    https://techcommunity.microsoft.com/rss

Run locally:
    fastmcp run ms-news-mcp-server.py --transport streamable-http --port 8002

Deploy to Azure Container Apps:
    Build the Docker image and deploy using the same pattern as budget-reports-mcp-server.py.
    Update MS_NEWS_MCP_SERVER_URL in your .env to point to the deployed endpoint.
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Try to import feedparser; if not available, fall back to httpx + xml parsing
# ---------------------------------------------------------------------------
try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

try:
    import xml.etree.ElementTree as ET
    ET_AVAILABLE = True
except ImportError:
    ET_AVAILABLE = False

# ---------------------------------------------------------------------------
# Server initialisation
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="MicrosoftNewsRSSServer",
    instructions=(
        "Provides access to Microsoft-published news articles from official RSS feeds. "
        "Use these tools to retrieve AI, Azure, Microsoft 365, GitHub, Copilot, and "
        "other Microsoft technology news published within a specified date range."
    ),
)

# ---------------------------------------------------------------------------
# RSS feed definitions
# ---------------------------------------------------------------------------

RSS_FEEDS = {
    "azure_blog": {
        "url": "https://azure.microsoft.com/en-us/blog/feed/",
        "source_name": "Azure Blog",
        "source_domain": "azure.microsoft.com",
    },
    "microsoft_blog": {
        "url": "https://blogs.microsoft.com/feed/",
        "source_name": "Microsoft Blog",
        "source_domain": "blogs.microsoft.com",
    },
    "tech_community": {
        "url": "https://techcommunity.microsoft.com/rss",
        "source_name": "Microsoft Tech Community",
        "source_domain": "techcommunity.microsoft.com",
    },
}

# Topics to filter for relevance
RELEVANT_KEYWORDS = [
    "AI", "artificial intelligence", "machine learning", "Azure", "OpenAI",
    "Copilot", "GitHub", "Microsoft 365", "Teams", "cloud", "security",
    "Power Platform", "Dynamics", "Fabric", "Sentinel", "Defender",
    "infrastructure", "compute", "storage", "containers", "Kubernetes",
    "developer", "API", "SDK", "release", "launch", "update", "new",
    "announcement", "preview", "generally available", "GA", "integration",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse a date string into a UTC-aware datetime. Returns None on failure."""
    if not date_str:
        return None
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _is_in_date_range(pub_date: Optional[datetime], start: datetime, end: datetime) -> bool:
    """Return True if pub_date falls within [start, end] inclusive."""
    if pub_date is None:
        return False
    pub_utc = pub_date.astimezone(timezone.utc).replace(tzinfo=None)
    start_utc = start.replace(tzinfo=None)
    end_utc = end.replace(tzinfo=None)
    return start_utc <= pub_utc <= end_utc


def _is_relevant(title: str, description: str) -> bool:
    """Return True if the article appears relevant to Microsoft technology topics."""
    combined = (title + " " + description).lower()
    return any(kw.lower() in combined for kw in RELEVANT_KEYWORDS)


def _fetch_feed_with_feedparser(feed_url: str, source_name: str, start: datetime, end: datetime) -> list:
    """Fetch and parse an RSS feed using feedparser."""
    articles = []
    try:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = getattr(entry, "title", "")
            link = getattr(entry, "link", "")
            pub_date_str = getattr(entry, "published", "") or getattr(entry, "updated", "")
            description = getattr(entry, "summary", "") or getattr(entry, "description", "")

            pub_date = _parse_date(pub_date_str)
            if not _is_in_date_range(pub_date, start, end):
                continue
            if not _is_relevant(title, description):
                continue

            date_str = pub_date.strftime("%Y-%m-%d") if pub_date else ""
            articles.append({
                "title": title,
                "url": link,
                "date": date_str,
                "source": source_name,
            })
    except Exception as exc:
        print(f"[MicrosoftNewsRSS] feedparser error for {feed_url}: {exc}")
    return articles


def _fetch_feed_with_httpx(feed_url: str, source_name: str, start: datetime, end: datetime) -> list:
    """Fetch and parse an RSS feed using httpx + ElementTree fallback."""
    articles = []
    try:
        resp = httpx.get(feed_url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        channel = root.find("channel")
        if channel is None:
            # Try Atom format
            items = root.findall("atom:entry", ns)
        else:
            items = channel.findall("item")

        for item in items:
            title_el = item.find("title") or item.find("atom:title", ns)
            link_el = item.find("link") or item.find("atom:link", ns)
            pub_el = item.find("pubDate") or item.find("atom:published", ns) or item.find("atom:updated", ns)
            desc_el = item.find("description") or item.find("atom:summary", ns)

            title = title_el.text.strip() if title_el is not None and title_el.text else ""
            link = link_el.text.strip() if link_el is not None and link_el.text else (
                link_el.get("href", "") if link_el is not None else ""
            )
            pub_date_str = pub_el.text.strip() if pub_el is not None and pub_el.text else ""
            description = desc_el.text or "" if desc_el is not None else ""

            pub_date = _parse_date(pub_date_str)
            if not _is_in_date_range(pub_date, start, end):
                continue
            if not _is_relevant(title, description):
                continue

            date_str = pub_date.strftime("%Y-%m-%d") if pub_date else ""
            articles.append({
                "title": title,
                "url": link,
                "date": date_str,
                "source": source_name,
            })
    except Exception as exc:
        print(f"[MicrosoftNewsRSS] httpx parse error for {feed_url}: {exc}")
    return articles


def _fetch_feed(feed_key: str, start_date: str, end_date: str) -> list:
    """Fetch articles from a named feed filtered by date range."""
    feed_cfg = RSS_FEEDS.get(feed_key)
    if not feed_cfg:
        return []

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
        end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    except ValueError:
        return []

    feed_url = feed_cfg["url"]
    source_name = feed_cfg["source_name"]

    if FEEDPARSER_AVAILABLE:
        return _fetch_feed_with_feedparser(feed_url, source_name, start, end)
    else:
        return _fetch_feed_with_httpx(feed_url, source_name, start, end)


# ---------------------------------------------------------------------------
# Tool 1 — Fetch from all RSS feeds
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def fetch_microsoft_news(start_date: str, end_date: str) -> dict:
    """
    Fetch Microsoft technology news from all official RSS feeds filtered to the provided date range.

    Args:
        start_date: Start of date range in YYYY-MM-DD format (inclusive).
        end_date:   End of date range in YYYY-MM-DD format (inclusive).

    Returns a consolidated list of articles from Azure Blog, Microsoft Blog, and Tech Community.
    Articles are filtered to the specified date range and relevant Microsoft technology topics.
    """
    all_articles = []
    seen_urls = set()

    for feed_key in RSS_FEEDS:
        articles = _fetch_feed(feed_key, start_date, end_date)
        for article in articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_articles.append(article)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_articles": len(all_articles),
        "articles": all_articles,
    }


# ---------------------------------------------------------------------------
# Tool 2 — Fetch Azure Blog only
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def fetch_azure_blog(start_date: str, end_date: str) -> dict:
    """
    Fetch articles from the Azure Blog RSS feed filtered to the provided date range.

    Args:
        start_date: Start of date range in YYYY-MM-DD format (inclusive).
        end_date:   End of date range in YYYY-MM-DD format (inclusive).

    Returns articles from https://azure.microsoft.com/en-us/blog/feed/
    """
    articles = _fetch_feed("azure_blog", start_date, end_date)
    return {
        "feed": "Azure Blog",
        "start_date": start_date,
        "end_date": end_date,
        "total_articles": len(articles),
        "articles": articles,
    }


# ---------------------------------------------------------------------------
# Tool 3 — Fetch Microsoft Blog only
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def fetch_microsoft_blog(start_date: str, end_date: str) -> dict:
    """
    Fetch articles from the Microsoft Blog RSS feed filtered to the provided date range.

    Args:
        start_date: Start of date range in YYYY-MM-DD format (inclusive).
        end_date:   End of date range in YYYY-MM-DD format (inclusive).

    Returns articles from https://blogs.microsoft.com/feed/
    """
    articles = _fetch_feed("microsoft_blog", start_date, end_date)
    return {
        "feed": "Microsoft Blog",
        "start_date": start_date,
        "end_date": end_date,
        "total_articles": len(articles),
        "articles": articles,
    }


# ---------------------------------------------------------------------------
# Tool 4 — Fetch Tech Community only
# ---------------------------------------------------------------------------

@mcp.tool(
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def fetch_tech_community(start_date: str, end_date: str) -> dict:
    """
    Fetch articles from the Microsoft Tech Community RSS feed filtered to the provided date range.

    Args:
        start_date: Start of date range in YYYY-MM-DD format (inclusive).
        end_date:   End of date range in YYYY-MM-DD format (inclusive).

    Returns articles from https://techcommunity.microsoft.com/rss
    """
    articles = _fetch_feed("tech_community", start_date, end_date)
    return {
        "feed": "Microsoft Tech Community",
        "start_date": start_date,
        "end_date": end_date,
        "total_articles": len(articles),
        "articles": articles,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("Microsoft News RSS MCP Server")
    print("=" * 70)
    print("Configured feeds:")
    for key, cfg in RSS_FEEDS.items():
        print(f"  {key}: {cfg['url']}")
    print("Available tools:")
    print("  1. fetch_microsoft_news(start_date, end_date)")
    print("  2. fetch_azure_blog(start_date, end_date)")
    print("  3. fetch_microsoft_blog(start_date, end_date)")
    print("  4. fetch_tech_community(start_date, end_date)")
    print("=" * 70)
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8002"))
    print(f"Starting server on http://{host}:{port}")
    print("=" * 70)
    mcp.run(transport="streamable-http", host=host, port=port)
