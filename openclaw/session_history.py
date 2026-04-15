"""
Session History API Client
Session event history fetching with cursor-based pagination.
Based on: src/assistant/sessionHistory.ts (87 lines)
"""
"""
Session History API Client
Session event history fetching with cursor-based pagination.
Based on: src/assistant/sessionHistory.ts (87 lines)

Design patterns:
- Cursor-based pagination (first_id → before_id) for efficient history traversal
- Auth context reuse across pages (avoid re-authenticating per-request)
- Page generators for memory-efficient streaming of large histories
- Optional event filtering by type, time range, and content search
"""
from dataclasses import dataclass, field
from typing import Any, Optional

try:
    import httpx as _httpx
    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False
    import urllib.request as _urllib
    import urllib.parse as _urllib_parse
    import json as _json

# Constants
HISTORY_PAGE_SIZE = 100


@dataclass
class HistoryPage:
    """
    A page of session history events.

    Attributes:
        events: Chronological list of SDK messages in this page.
        first_id: Oldest event ID → before_id cursor for next-older page.
        has_more: True if older events exist beyond this page.
    """
    events: list[dict[str, Any]] = field(default_factory=list)
    first_id: Optional[str] = None
    has_more: bool = False


@dataclass
class HistoryAuthCtx:
    """
    Authentication context for history API requests.
    Prepared once and reused across page fetches.
    """
    base_url: str
    headers: dict[str, str]


class SessionHistoryError(Exception):
    """Base exception for session history operations."""
    pass


class HistoryFetchError(SessionHistoryError):
    """HTTP fetch failed."""
    def __init__(self, status: Optional[int] = None, message: str = ""):
        self.status = status
        super().__init__(f"History fetch failed: {status or 'network error'} {message}")


async def create_history_auth_ctx(
    session_id: str,
    *,
    access_token: str,
    base_api_url: str,
    org_uuid: Optional[str] = None,
) -> HistoryAuthCtx:
    """
    Create authentication context for session history API.

    Args:
        session_id: The session ID to fetch history for.
        access_token: OAuth access token.
        base_api_url: Base API URL (e.g., https://api.anthropic.com).
        org_uuid: Optional organization UUID.

    Returns:
        HistoryAuthCtx with base URL and headers ready for API calls.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "anthropic-beta": "ccr-byoc-2025-07-29",
    }
    if org_uuid:
        headers["x-organization-uuid"] = org_uuid

    return HistoryAuthCtx(
        base_url=f"{base_api_url}/v1/sessions/{session_id}/events",
        headers=headers,
    )


async def _fetch_page(
    ctx: HistoryAuthCtx,
    params: dict[str, Any],
    label: str,
    timeout: float = 15.0,
) -> Optional[HistoryPage]:
    """
    Fetch a single page of history events.

    Args:
        ctx: Authentication context.
        params: Query parameters.
        label: Label for logging/debugging.
        timeout: Request timeout in seconds.

    Returns:
        HistoryPage if successful, None on error.
    """
    if _HTTPX_AVAILABLE:
        import asyncio
        try:
            import httpx
            async def _do_fetch():
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        ctx.base_url,
                        headers=ctx.headers,
                        params=params,
                        timeout=timeout,
                        follow_redirects=True,
                    )
                    return resp
            resp = asyncio.run(_do_fetch())
        except Exception:
            return None
    else:
        # Fallback to urllib (synchronous only)
        url = f"{ctx.base_url}?{_urllib_parse.urlencode(params)}"
        req = _urllib.Request(url, headers=ctx.headers)
        try:
            with _urllib.urlopen(req, timeout=timeout) as response:
                resp_data = response.read()
                data = _json.loads(resp_data)
        except Exception:
            return None

        events = data.get("data", [])
        if not isinstance(events, list):
            events = []
        return HistoryPage(
            events=events,
            first_id=data.get("first_id"),
            has_more=bool(data.get("has_more")),
        )
        return None  # unreachable

    if resp.status_code != 200:
        return None

    try:
        data = resp.json()
    except Exception:
        return None

    events = data.get("data", [])
    if not isinstance(events, list):
        events = []

    return HistoryPage(
        events=events,
        first_id=data.get("first_id"),
        has_more=bool(data.get("has_more")),
    )


async def fetch_latest_events(
    ctx: HistoryAuthCtx,
    limit: int = HISTORY_PAGE_SIZE,
) -> Optional[HistoryPage]:
    """
    Fetch the newest events (anchored to latest).

    Uses anchor_to_latest parameter to get the most recent `limit` events
    in chronological order. has_more=True means older events exist.

    Args:
        ctx: Authentication context.
        limit: Maximum number of events to fetch.

    Returns:
        HistoryPage with newest events, or None on failure.
    """
    return await _fetch_page(
        ctx,
        {"limit": limit, "anchor_to_latest": True},
        "fetchLatestEvents",
    )


async def fetch_older_events(
    ctx: HistoryAuthCtx,
    before_id: str,
    limit: int = HISTORY_PAGE_SIZE,
) -> Optional[HistoryPage]:
    """
    Fetch older events before a cursor.

    Uses the first_id from a previous page as the before_id cursor
    to fetch the next older page of events.

    Args:
        ctx: Authentication context.
        before_id: Cursor from previous page's first_id.
        limit: Maximum number of events to fetch.

    Returns:
        HistoryPage with older events, or None on failure.
    """
    return await _fetch_page(
        ctx,
        {"limit": limit, "before_id": before_id},
        "fetchOlderEvents",
    )


async def fetch_all_events(
    ctx: HistoryAuthCtx,
    limit: int = HISTORY_PAGE_SIZE,
    max_pages: int = 100,
) -> AsyncIterator[HistoryPage]:
    """
    Fetch all events page by page.

    Generator that yields pages starting from newest,
    following has_more/first_id cursor until exhausted or max_pages reached.

    Args:
        ctx: Authentication context.
        limit: Events per page.
        max_pages: Safety limit on pages to fetch.

    Yields:
        HistoryPage objects from newest to oldest.
    """
    page = await fetch_latest_events(ctx, limit)
    if not page:
        return

    yield page

    pages_fetched = 1
    while page.has_more and pages_fetched < max_pages:
        if page.first_id is None:
            break

        page = await fetch_older_events(ctx, page.first_id, limit)
        if not page:
            break

        yield page
        pages_fetched += 1


async def fetch_events_count(
    ctx: HistoryAuthCtx,
    limit: int = HISTORY_PAGE_SIZE,
) -> int:
    """
    Count total events by fetching all pages.

    Warning: Expensive for large histories. Use sparingly.

    Args:
        ctx: Authentication context.
        limit: Events per page.

    Returns:
        Total count of events available.
    """
    total = 0
    async for page in fetch_all_events(ctx, limit):
        total += len(page.events)
    return total


@dataclass
class HistoryEventFilter:
    """Filter criteria for history events."""
    # Filter by event type (e.g., "user", "assistant", "tool_use", "tool_result")
    event_types: Optional[list[str]] = None
    # Filter by time range (Unix timestamps)
    after_timestamp: Optional[float] = None
    before_timestamp: Optional[float] = None
    # Search in event content
    search_text: Optional[str] = None


def filter_events(
    events: list[dict[str, Any]],
    filter_fn: HistoryEventFilter,
) -> list[dict[str, Any]]:
    """
    Filter events by criteria.

    Args:
        events: List of event dictionaries.
        filter_fn: Filter criteria.

    Returns:
        Filtered events matching all criteria.
    """
    result = events

    if filter_fn.event_types:
        result = [
            e for e in result
            if e.get("type") in filter_fn.event_types
        ]

    if filter_fn.after_timestamp is not None:
        result = [
            e for e in result
            if e.get("timestamp", 0) >= filter_fn.after_timestamp
        ]

    if filter_fn.before_timestamp is not None:
        result = [
            e for e in result
            if e.get("timestamp", 0) <= filter_fn.before_timestamp
        ]

    if filter_fn.search_text:
        search = filter_fn.search_text.lower()
        result = [
            e for e in result
            if search in str(e.get("content", "")).lower()
            or search in str(e.get("text", "")).lower()
        ]

    return result


if __name__ == "__main__":
    # Quick validation test
    print("session_history.py - OK")
