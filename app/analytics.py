"""Simple server-side analytics middleware.

Logs every request to SQLite: path, IP country (via ip-api.com), user-agent,
bot detection, timestamp. Powers the /stats page.
"""
import asyncio
import re
import time
import aiosqlite
import httpx
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

DB_PATH = __import__("os").environ.get("DB_PATH", "/data/progress.db")

# Bot detection — common crawlers / scanners
BOT_PATTERNS = re.compile(
    r"(bot|crawl|spider|slurp|facebookexternalhit|whatsapp|telegram|"
    r"twitterbot|linkedinbot|googlebot|bingbot|yandex|baidu|duckduck|"
    r"semrush|ahrefs|mj12bot|dotbot|pingdom|uptimerobot|curl|wget|python-requests|"
    r"go-http-client|libwww|okhttp)",
    re.IGNORECASE,
)

# Simple geo cache to avoid hammering ip-api.com (free: 1000/day)
_geo_cache: dict[str, str] = {}


async def _get_country(ip: str) -> str:
    if not ip or ip in ("127.0.0.1", "::1"):
        return "local"
    if ip in _geo_cache:
        return _geo_cache[ip]
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"http://ip-api.com/json/{ip}?fields=countryCode")
            if r.status_code == 200:
                country = r.json().get("countryCode", "??")
                _geo_cache[ip] = country
                return country
    except Exception:
        pass
    return "??"


async def _log_hit(path: str, ip: str, ua: str, is_bot: bool, country: str):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS hits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts INTEGER NOT NULL,
                    path TEXT NOT NULL,
                    ip TEXT,
                    country TEXT,
                    ua TEXT,
                    is_bot INTEGER DEFAULT 0
                )
            """)
            await db.execute(
                "INSERT INTO hits (ts, path, ip, country, ua, is_bot) VALUES (?,?,?,?,?,?)",
                (int(time.time()), path, ip[:45] if ip else "", country, ua[:200] if ua else "", int(is_bot)),
            )
            await db.commit()
    except Exception:
        pass  # Never crash the app for analytics


class AnalyticsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip static files and health checks
        path = request.url.path
        if path.startswith("/static") or path in ("/health", "/favicon.ico"):
            return await call_next(request)

        ua = request.headers.get("user-agent", "")
        is_bot = bool(BOT_PATTERNS.search(ua))

        # Real IP — Fly.io puts it in Fly-Client-IP header
        ip = (
            request.headers.get("fly-client-ip")
            or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (request.client.host if request.client else "")
        )

        # Fire-and-forget geo lookup + logging (don't slow the request)
        country = _geo_cache.get(ip, "??")
        asyncio.create_task(_log_hit(path, ip, ua, is_bot, country))
        if country == "??" and ip and ip != "127.0.0.1":
            asyncio.create_task(self._resolve_and_relog(path, ip, ua, is_bot))

        return await call_next(request)

    async def _resolve_and_relog(self, path, ip, ua, is_bot):
        country = await _get_country(ip)
        await _log_hit(path, ip, ua, is_bot, country)
