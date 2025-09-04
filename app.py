import os
import time
import logging
from datetime import datetime, timezone
from typing import List, Tuple

import requests
from dateutil import parser as dtparser
from flask import Flask, Response, jsonify
from icalendar import Calendar, Event, vCalAddress, vText

app = Flask(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

SONARR_ICAL_URL = os.getenv("SONARR_ICAL_URL", "").strip()
RADARR_ICAL_URL = os.getenv("RADARR_ICAL_URL", "").strip()
REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "1800"))  # 30 min default
CAL_NAME = os.getenv("CAL_NAME", "Radarr+Sonarr")
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() == "true"
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "12"))  # seconds
TZ_NAME = os.getenv("TZ", "America/Chicago")

# Simple in-memory cache
_cache = {
    "last_fetched": 0.0,
    "calendar_bytes": b"",
    "source_status": {}
}


def _fetch_ics(url: str) -> Tuple[str, bytes]:
    """Fetch ICS bytes from a URL; returns (label, bytes)."""
    if not url:
        return ("", b"")
    label = "sonarr" if "sonarr" in url.lower() else ("radarr" if "radarr" in url.lower() else "source")
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT, verify=VERIFY_SSL)
        r.raise_for_status()
        return (label, r.content)
    except requests.RequestException as e:
        app.logger.warning("Failed fetching %s: %s", label, e)
        return (label, b"")


def _parse_events(cal_bytes: bytes, source_label: str) -> List[Event]:
    """Parse VEVENTs from bytes with unique, source-prefixed UIDs."""
    if not cal_bytes:
        return []

    try:
        cal = Calendar.from_ical(cal_bytes)
    except Exception as e:
        app.logger.warning("Failed parsing ICS from %s: %s", source_label, e)
        return []

    events = []
    for comp in cal.walk("VEVENT"):
        try:
            ev = Event()
            # Copy standard fields safely
            for key in comp.keys():
                ev.add(key, comp.get(key))

            # Ensure UID uniqueness across sources
            uid = str(comp.get("UID") or "")
            if uid:
                ev["UID"] = f"{source_label}:{uid}"
            else:
                # Fallback UID
                start = comp.get("DTSTART")
                stamp = comp.get("DTSTAMP") or datetime.now(timezone.utc)
                ev["UID"] = f"{source_label}:{start}:{stamp}:{hash(comp.to_ical())}"

            # Normalize DTSTART/DTEND to be safe
            # (icalendar may store as vDDDTypes; we just ensure they are present)
            # If DTSTART is missing, skip event
            if not comp.get("DTSTART"):
                continue

            events.append(ev)
        except Exception as e:
            app.logger.debug("Skipping malformed event from %s: %s", source_label, e)
            continue
    return events


def _merge_and_build_calendar() -> bytes:
    """Fetch Sonarr/Radarr ICS, merge events, and return a single ICS bytes."""
    sources = []
    statuses = {}

    if SONARR_ICAL_URL:
        lbl, c = _fetch_ics(SONARR_ICAL_URL)
        statuses[lbl or "sonarr"] = "ok" if c else "error"
        sources.append((lbl or "sonarr", c))
    if RADARR_ICAL_URL:
        lbl, c = _fetch_ics(RADARR_ICAL_URL)
        statuses[lbl or "radarr"] = "ok" if c else "error"
        sources.append((lbl or "radarr", c))

    # Parse and collect events
    all_events: List[Event] = []
    for label, blob in sources:
        all_events.extend(_parse_events(blob, label))

    # De-duplicate by UID (keep latest DTSTAMP if duplicates)
    by_uid = {}
    for ev in all_events:
        uid = str(ev.get("UID"))
        existing = by_uid.get(uid)
        if not existing:
            by_uid[uid] = ev
        else:
            # Keep one with latest DTSTAMP (if available)
            def stamp(e):
                s = e.get("DTSTAMP")
                try:
                    return dtparser.parse(str(s)) if s else datetime.fromtimestamp(0, tz=timezone.utc)
                except Exception:
                    return datetime.fromtimestamp(0, tz=timezone.utc)
            if stamp(ev) > stamp(existing):
                by_uid[uid] = ev

    merged = Calendar()
    merged.add("prodid", "-//Merged Radarr+Sonarr//ical-merge//EN")
    merged.add("version", "2.0")
    merged.add("X-WR-CALNAME", CAL_NAME)
    merged.add("X-WR-TIMEZONE", TZ_NAME)

    # Sort events by DTSTART
    def start_key(e: Event):
        try:
            dt = e.get("DTSTART").dt
            # Convert date to datetime at midnight for sorting consistency
            if hasattr(dt, "year") and not hasattr(dt, "hour"):
                return datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)
            return dt
        except Exception:
            return datetime.max.replace(tzinfo=timezone.utc)

    for ev in sorted(by_uid.values(), key=start_key):
        merged.add_component(ev)

    # Attach fetch status as X- properties in VCALENDAR (optional/debug)
    for src, st in statuses.items():
        merged.add(f"X-MERGE-{src.upper()}", st)

    return merged.to_ical()


def _get_cached_calendar() -> Tuple[bytes, dict]:
    now = time.time()
    if (now - _cache["last_fetched"]) < REFRESH_SECONDS and _cache["calendar_bytes"]:
        return _cache["calendar_bytes"], _cache["source_status"]

    cal_bytes = _merge_and_build_calendar()
    _cache["calendar_bytes"] = cal_bytes
    _cache["last_fetched"] = now
    # Source status already embedded as X-MERGE-*; expose minimal status too
    _cache["source_status"] = {"refreshed_at": datetime.now(timezone.utc).isoformat()}
    return cal_bytes, _cache["source_status"]


@app.route("/")
def index():
    return jsonify({
        "name": "Radarr+Sonarr iCal Merge",
        "calendar": "/calendar",
        "health": "/health",
        "cache_ttl_seconds": REFRESH_SECONDS,
        "tz": TZ_NAME,
        "cal_name": CAL_NAME
    })


@app.route("/health")
def health():
    # Lightweight ping + indicates whether cache is warm
    is_warm = bool(_cache["calendar_bytes"])
    return jsonify({
        "status": "ok",
        "cache_warm": is_warm,
        "last_fetched": _cache["last_fetched"]
    })


@app.route("/calendar")
def calendar():
    cal_bytes, _ = _get_cached_calendar()
    headers = {
        "Content-Type": "text/calendar; charset=utf-8",
        "Content-Disposition": f'attachment; filename="{CAL_NAME.replace(" ", "_")}.ics"',
        "X-Generated-At": datetime.now(timezone.utc).isoformat()
    }
    return Response(cal_bytes, headers=headers)


if __name__ == "__main__":
    # Dev run (Dockerfile uses gunicorn in production)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))