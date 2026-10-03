from __future__ import annotations

import json
import threading
import time
from urllib.parse import urlencode
from urllib.request import Request as URLRequest, urlopen

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/maps", tags=["maps"])

_NOMINATIM = "https://nominatim.openstreetmap.org"
_UA = "KAVRON-Intelligence/5.0 (local surveillance demo)"
_lock = threading.Lock()
_last_request = 0.0
_cache: dict[str, tuple[float, object]] = {}
_CACHE_TTL = 300.0


def _get_json(path: str, params: dict[str, str]) -> object:
    global _last_request
    key = path + "?" + urlencode(sorted(params.items()))
    now = time.monotonic()
    cached = _cache.get(key)
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1]

    # Public Nominatim is capacity-limited. Keep requests at <= 1/sec.
    with _lock:
        wait = 1.05 - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        req = URLRequest(
            _NOMINATIM + path + "?" + urlencode(params),
            headers={"User-Agent": _UA, "Accept": "application/json"},
        )
        try:
            with urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Map geocoding service unavailable: {exc}") from exc
        _last_request = time.monotonic()
    _cache[key] = (_last_request, data)
    return data


@router.get("/search")
def search_map(
    q: str = Query(min_length=2, max_length=160),
):
    data = _get_json("/search", {
        "q": q,
        "format": "jsonv2",
        "limit": "6",
        "addressdetails": "1",
    })
    return {"results": data}


@router.get("/reverse")
def reverse_map(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
):
    data = _get_json("/reverse", {
        "lat": str(lat),
        "lon": str(lon),
        "format": "jsonv2",
        "zoom": "18",
        "addressdetails": "1",
    })
    return data


@router.get("/config")
def map_config():
    return {
        "provider": "OpenStreetMap",
        "tile_url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attribution": "© OpenStreetMap contributors",
        "geocoding": "Nominatim",
        "note": "Use the public geocoder lightly; production deployments should use a dedicated geocoding provider or self-hosted service.",
    }
