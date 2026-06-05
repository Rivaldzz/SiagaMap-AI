"""
Disasters Router — Serves real-time BMKG earthquake data.
"""

from fastapi import APIRouter, HTTPException
import logging

from backend.services.bmkg_service import get_disasters, clear_cache, get_news

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["disasters"])


@router.get("/disasters")
async def list_disasters():
    """
    Get all current disasters from BMKG data.
    Returns cached data if available, fetches fresh data otherwise.
    """
    try:
        disasters = await get_disasters()
        return disasters
    except Exception as e:
        logger.error(f"Error fetching disasters: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil data bencana dari BMKG")


@router.get("/disasters/refresh")
async def refresh_disasters():
    """Force refresh the disaster data cache."""
    try:
        clear_cache()
        disasters = await get_disasters()
        return {
            "message": "Data berhasil diperbarui",
            "count": len(disasters),
            "data": disasters,
        }
    except Exception as e:
        logger.error(f"Error refreshing disasters: {e}")
        raise HTTPException(status_code=500, detail="Gagal memperbarui data bencana")


@router.get("/news")
async def list_news():
    """
    Get latest disaster news.
    """
    try:
        news = await get_news()
        return news
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil berita bencana")

