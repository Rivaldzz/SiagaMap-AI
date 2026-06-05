"""
BMKG Data Service — Fetches and parses real-time disaster data
from the BMKG Open API (Badan Meteorologi, Klimatologi, dan Geofisika).
"""

import httpx
import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ─── BMKG API Endpoints ─────────────────────────────────────────

BMKG_AUTOGEMPA_URL = "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json"
BMKG_GEMPA_TERKINI_URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json"
BMKG_GEMPA_DIRASAKAN_URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json"

# ─── Cache ───────────────────────────────────────────────────────

_cache: Dict[str, Any] = {
    "data": [],
    "last_fetched": None,
}
_news_cache: Dict[str, Any] = {
    "data": [],
    "last_fetched": None,
}
CACHE_TTL_SECONDS = 60  # Refresh every 60 seconds

# ─── Simulated Disaster Data (Non-Earthquake) ────────────────────

SUPPLEMENTAL_DISASTERS = [
    {
        "id": "sim_vol_001",
        "type": "Erupsi Gunung Api",
        "location": "Gunung Merapi, Jawa Tengah — Status SIAGA (Level III). Guguran lava pijar sejauh 1.5 km.",
        "coordinates": [-7.54, 110.44],
        "time": "Terkini",
        "risk_level": "Tinggi",
        "depth": "0 km",
        "magnitude": 0.0,
    },
    {
        "id": "sim_vol_002",
        "type": "Erupsi Gunung Api",
        "location": "Gunung Anak Krakatau, Selat Sunda — Status WASPADA (Level II). Aktivitas kegempaan fluktuatif.",
        "coordinates": [-6.102, 105.423],
        "time": "Terkini",
        "risk_level": "Sedang",
        "depth": "0 km",
        "magnitude": 0.0,
    },
    {
        "id": "sim_flood_001",
        "type": "Banjir",
        "location": "Dayeuhkolot, Kabupaten Bandung — Luapan sungai Citarum merendam pemukiman warga setinggi 1 meter.",
        "coordinates": [-7.005, 107.621],
        "time": "Terkini",
        "risk_level": "Tinggi",
        "depth": None,
        "magnitude": None,
    },
    {
        "id": "sim_flood_002",
        "type": "Banjir",
        "location": "Cilincing, Jakarta Utara — Genangan banjir rob setinggi 40 cm membasahi pemukiman pesisir.",
        "coordinates": [-6.125, 106.842],
        "time": "Terkini",
        "risk_level": "Sedang",
        "depth": None,
        "magnitude": None,
    },
    {
        "id": "sim_fire_001",
        "type": "Kebakaran Hutan",
        "location": "Ogan Ilir, Sumatera Selatan — Pemadaman titik api karhutla di lahan gambut oleh Manggala Agni.",
        "coordinates": [-3.224, 104.755],
        "time": "Terkini",
        "risk_level": "Sedang",
        "depth": None,
        "magnitude": None,
    },
    {
        "id": "sim_fire_002",
        "type": "Kebakaran Hutan",
        "location": "Dumai, Riau — Karhutla seluas 10 hektar terdeteksi satelit Terra/Aqua.",
        "coordinates": [1.688, 101.445],
        "time": "Terkini",
        "risk_level": "Tinggi",
        "depth": None,
        "magnitude": None,
    },
    {
        "id": "sim_slide_001",
        "type": "Tanah Longsor",
        "location": "Cisolok, Sukabumi, Jawa Barat — Longsoran tanah tebing menutup jalan penghubung antar kecamatan.",
        "coordinates": [-6.924, 106.932],
        "time": "Terkini",
        "risk_level": "Sedang",
        "depth": None,
        "magnitude": None,
    },
    {
        "id": "sim_weather_001",
        "type": "Prakiraan Cuaca Ekstrem",
        "location": "Kota Surabaya, Jawa Timur — Waspada potensi angin puting beliung dan hujan es berdurasi singkat.",
        "coordinates": [-7.258, 112.752],
        "time": "Hari ini",
        "risk_level": "Rendah",
        "depth": None,
        "magnitude": None,
    }
]

# ─── Mock Fallback News ──────────────────────────────────────────

MOCK_NEWS = [
    {
        "id": "news_mock_1",
        "title": "BMKG Himbau Waspada Potensi Cuaca Ekstrem Pancaroba di Jawa Barat",
        "link": "https://www.bmkg.go.id/berita/waspada-cuaca-ekstrem",
        "date": "Hari ini, 09:15 WIB",
        "category": "Cuaca Ekstrem",
        "summary": "BMKG mengeluarkan rilis resmi potensi cuaca ekstrem berupa hujan es, angin kencang, dan hujan lebat berdurasi singkat selama fase pancaroba di sebagian wilayah Bogor, Bandung, dan Sukabumi."
    },
    {
        "id": "news_mock_2",
        "title": "Klarifikasi BMKG: Isu Gempa Megathrust 9.0 SR di Selat Sunda Besok Adalah Hoaks",
        "link": "https://www.bmkg.go.id/berita/klarifikasi-isu-gempa-megathrust-selat-sunda",
        "date": "Hari ini, 07:30 WIB",
        "category": "Hoax Buster",
        "summary": "Kepala BMKG menegaskan bahwa pesan berantai yang mengklaim tsunami setinggi 20 meter di pesisir Banten akibat gempa megathrust besok adalah hoaks. BMKG menghimbau masyarakat tetap tenang."
    },
    {
        "id": "news_mock_3",
        "title": "Analisis Aktivitas Vulkanik Gunung Api Ruang Meningkat ke Level Awas (Level IV)",
        "link": "https://vsi.esdm.go.id/berita/gunung-ruang-level-awas",
        "date": "Kemarin, 18:40 WIB",
        "category": "Erupsi Gunung Api",
        "summary": "PVMBG menaikkan status aktivitas Gunung Ruang di Sulawesi Utara menjadi Awas. Masyarakat dihimbau menjauhi radius aman 6 km karena adanya potensi awan panas guguran."
    },
    {
        "id": "news_mock_4",
        "title": "Banjir Luapan Sungai Citarum Merendam Ratusan Rumah di Dayeuhkolot Bandung",
        "link": "https://www.bnpb.go.id/berita/banjir-citarum-dayeuhkolot",
        "date": "Kemarin, 14:10 WIB",
        "category": "Banjir",
        "summary": "Curah hujan yang ekstrim menyebabkan tanggul sungai Citarum meluap dan merendam pemukiman warga setinggi 1 meter. BPBD Jawa Barat telah mendirikan posko darurat bencana."
    },
    {
        "id": "news_mock_5",
        "title": "Kebakaran Hutan dan Lahan di Ogan Ilir Sumsel Mulai Terkendali",
        "link": "https://www.bnpb.go.id/berita/karhutla-ogan-ilir",
        "date": "2 hari lalu",
        "category": "Kebakaran Hutan",
        "summary": "Manggala Agni bersama TNI/Polri berhasil memadamkan titik api karhutla seluas 15 hektar di wilayah Ogan Ilir Sumatra Selatan menggunakan metode water bombing."
    }
]



# ─── Fallback Mock Data ─────────────────────────────────────────

FALLBACK_DATA = [
    {
        "id": "fallback_001",
        "type": "Gempa Bumi",
        "magnitude": 5.2,
        "depth": "10 km",
        "location": "Pusat gempa berada di darat 28 km BaratDaya Cianjur, Jawa Barat",
        "coordinates": [-6.89, 107.01],
        "time": "Data BMKG tidak tersedia",
        "risk_level": "Sedang",
    },
    {
        "id": "fallback_002",
        "type": "Gempa Bumi",
        "magnitude": 3.8,
        "depth": "18 km",
        "location": "Pusat gempa berada di laut 45 km Tenggara Malang, Jawa Timur",
        "coordinates": [-8.35, 112.95],
        "time": "Data BMKG tidak tersedia",
        "risk_level": "Rendah",
    },
]


def _classify_risk(magnitude: Optional[float], depth_str: Optional[str]) -> str:
    """Determine risk level based on magnitude and depth."""
    if magnitude is None:
        return "Rendah"

    # Parse depth
    depth_km = 10.0  # default
    if depth_str:
        try:
            depth_km = float(depth_str.replace(" km", "").replace("Km", "").strip())
        except (ValueError, AttributeError):
            depth_km = 10.0

    # Risk classification logic
    if magnitude >= 7.0:
        return "Tinggi"
    elif magnitude >= 5.5:
        if depth_km <= 30:
            return "Tinggi"
        else:
            return "Sedang"
    elif magnitude >= 4.0:
        if depth_km <= 15:
            return "Sedang"
        else:
            return "Rendah"
    else:
        return "Rendah"


def _parse_coordinates(lat_str: str, lon_str: str) -> List[float]:
    """Parse BMKG coordinate strings like '-6.89' and '107.01' to [lat, lon]."""
    try:
        lat = float(lat_str)
        lon = float(lon_str)
        return [lat, lon]
    except (ValueError, TypeError):
        return [-2.5489, 118.0149]  # Center of Indonesia as fallback


def _parse_gempa_item(item: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Parse a single earthquake item from BMKG response."""
    magnitude = None
    magnitude_str = item.get("Magnitude", "")
    try:
        magnitude = float(magnitude_str)
    except (ValueError, TypeError):
        magnitude = None

    depth_str = item.get("Kedalaman", "")

    # Parse coordinates from "Lintang" and "Bujur" fields
    lat_str = item.get("Lintang", "0")
    lon_str = item.get("Bujur", "0")

    # BMKG uses formats like "-6.89" for latitude and "107.01 BT" for longitude
    try:
        lat = float(str(lat_str).replace(" LS", "").replace(" LU", "").strip())
        # Make southern latitudes negative
        if "LS" in str(lat_str):
            lat = -abs(lat)
        elif "LU" in str(lat_str):
            lat = abs(lat)
    except (ValueError, TypeError):
        lat = -2.5489

    try:
        lon = float(str(lon_str).replace(" BT", "").replace(" BB", "").strip())
    except (ValueError, TypeError):
        lon = 118.0149

    # Build timestamp string
    tanggal = item.get("Tanggal", "")
    jam = item.get("Jam", "")
    time_str = f"{tanggal} {jam}".strip() if tanggal else "Waktu tidak tersedia"

    location = item.get("Wilayah", item.get("Dirasakan", "Lokasi tidak diketahui"))

    risk_level = _classify_risk(magnitude, depth_str)

    return {
        "id": f"bmkg_{index:04d}_{datetime.now().strftime('%Y%m%d')}",
        "type": "Gempa Bumi",
        "magnitude": magnitude,
        "depth": depth_str if depth_str else None,
        "location": location,
        "coordinates": [lat, lon],
        "time": time_str,
        "risk_level": risk_level,
    }


async def fetch_bmkg_data() -> List[Dict[str, Any]]:
    """
    Fetch earthquake data from multiple BMKG endpoints.
    Returns a list of normalized disaster objects.
    """
    all_disasters: List[Dict[str, Any]] = []
    index_counter = 0

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Fetch auto-detected latest earthquake
        try:
            resp = await client.get(BMKG_AUTOGEMPA_URL)
            resp.raise_for_status()
            data = resp.json()

            # The autogempa endpoint returns: {"Infogempa": {"gempa": {...}}}
            gempa = data.get("Infogempa", {}).get("gempa", {})
            if gempa and isinstance(gempa, dict):
                parsed = _parse_gempa_item(gempa, index_counter)
                parsed["id"] = f"bmkg_auto_{datetime.now().strftime('%Y%m%d%H%M')}"
                all_disasters.append(parsed)
                index_counter += 1
                logger.info("Fetched autogempa data successfully")
        except Exception as e:
            logger.warning(f"Failed to fetch autogempa: {e}")

        # 2. Fetch recent earthquakes list
        try:
            resp = await client.get(BMKG_GEMPA_TERKINI_URL)
            resp.raise_for_status()
            data = resp.json()

            # gempaterkini returns: {"Infogempa": {"gempa": [...]}}
            gempa_list = data.get("Infogempa", {}).get("gempa", [])
            if isinstance(gempa_list, list):
                for item in gempa_list:
                    parsed = _parse_gempa_item(item, index_counter)
                    all_disasters.append(parsed)
                    index_counter += 1
                logger.info(f"Fetched {len(gempa_list)} recent earthquakes")
        except Exception as e:
            logger.warning(f"Failed to fetch gempaterkini: {e}")

        # 3. Fetch felt earthquakes
        try:
            resp = await client.get(BMKG_GEMPA_DIRASAKAN_URL)
            resp.raise_for_status()
            data = resp.json()

            gempa_list = data.get("Infogempa", {}).get("gempa", [])
            if isinstance(gempa_list, list):
                for item in gempa_list:
                    parsed = _parse_gempa_item(item, index_counter)
                    parsed["type"] = "Gempa Dirasakan"
                    all_disasters.append(parsed)
                    index_counter += 1
                logger.info(f"Fetched {len(gempa_list)} felt earthquakes")
        except Exception as e:
            logger.warning(f"Failed to fetch gempadirasakan: {e}")

    # Deduplicate by coordinates + time (within 1 minute)
    seen = set()
    unique_disasters = []
    for d in all_disasters:
        key = (
            round(d["coordinates"][0], 2),
            round(d["coordinates"][1], 2),
            d.get("time", "")[:20],
        )
        if key not in seen:
            seen.add(key)
            unique_disasters.append(d)

    if not unique_disasters:
        logger.warning("No data from BMKG, using fallback data")
        return FALLBACK_DATA + SUPPLEMENTAL_DISASTERS

    return unique_disasters + SUPPLEMENTAL_DISASTERS


async def get_disasters() -> List[Dict[str, Any]]:
    """
    Get disasters with caching. Returns cached data if within TTL,
    otherwise fetches fresh data from BMKG.
    """
    global _cache

    now = datetime.now()
    if (
        _cache["last_fetched"] is not None
        and _cache["data"]
        and (now - _cache["last_fetched"]).total_seconds() < CACHE_TTL_SECONDS
    ):
        return _cache["data"]

    try:
        data = await fetch_bmkg_data()
        _cache["data"] = data
        _cache["last_fetched"] = now
        logger.info(f"Cache refreshed with {len(data)} disasters")
        return data
    except Exception as e:
        logger.error(f"Error fetching BMKG data: {e}")
        if _cache["data"]:
            return _cache["data"]
        return FALLBACK_DATA + SUPPLEMENTAL_DISASTERS


def clear_cache():
    """Clear the BMKG data cache."""
    global _cache
    _cache = {"data": [], "last_fetched": None}


async def fetch_news_rss() -> List[Dict[str, Any]]:
    """
    Fetch and parse BMKG news RSS feed. Falls back to MOCK_NEWS if fails.
    """
    news_items = []
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get("https://www.bmkg.go.id/tag/berita/rss")
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                items = root.findall(".//item")
                for i, item in enumerate(items[:8]):  # limit to top 8
                    title = item.find("title").text if item.find("title") is not None else "Berita Bencana"
                    link = item.find("link").text if item.find("link") is not None else ""
                    pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                    desc = item.find("description").text if item.find("description") is not None else ""
                    
                    desc_clean = re.sub(r'<[^>]*>', '', desc).strip() if desc else ""
                    if len(desc_clean) > 200:
                        desc_clean = desc_clean[:200] + "..."
                        
                    date_display = pub_date
                    try:
                        date_display = pub_date.split(" +")[0]
                    except Exception:
                        pass
                    
                    category = "Info BMKG"
                    title_lower = title.lower()
                    if "gempa" in title_lower:
                        category = "Gempa Bumi"
                    elif "cuaca" in title_lower or "hujan" in title_lower or "angin" in title_lower:
                        category = "Cuaca"
                    elif "tsunami" in title_lower:
                        category = "Tsunami"
                    elif "vulkanik" in title_lower or "gunung" in title_lower or "letusan" in title_lower:
                        category = "Vulkanologi"
                    elif "gelombang" in title_lower or "laut" in title_lower:
                        category = "Maritim"
                    elif "hoaks" in title_lower or "hoax" in title_lower or "klarifikasi" in title_lower:
                        category = "Hoax Buster"
                        
                    news_items.append({
                        "id": f"rss_{i}_{datetime.now().strftime('%Y%m%d')}",
                        "title": title,
                        "link": link,
                        "date": date_display,
                        "category": category,
                        "summary": desc_clean if desc_clean else "Silakan klik selengkapnya untuk membaca berita."
                    })
                
                if news_items:
                    logger.info(f"Successfully fetched {len(news_items)} news items from BMKG RSS")
                    return news_items
        except Exception as e:
            logger.warning(f"Failed to fetch BMKG news RSS feed: {e}. Using simulated mock news.")
            
    return MOCK_NEWS


async def get_news() -> List[Dict[str, Any]]:
    """
    Get latest disaster news with caching.
    """
    global _news_cache

    now = datetime.now()
    if (
        _news_cache["last_fetched"] is not None
        and _news_cache["data"]
        and (now - _news_cache["last_fetched"]).total_seconds() < CACHE_TTL_SECONDS
    ):
        return _news_cache["data"]

    try:
        data = await fetch_news_rss()
        _news_cache["data"] = data
        _news_cache["last_fetched"] = now
        logger.info(f"News cache refreshed with {len(data)} items")
        return data
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        if _news_cache["data"]:
            return _news_cache["data"]
        return MOCK_NEWS

