"""
Pydantic models for SiagaMap AI API request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ─── Disaster Data ───────────────────────────────────────────────

class DisasterInfo(BaseModel):
    """Schema for a single disaster event."""
    id: str
    type: str  # e.g., "Gempa Bumi", "Tsunami", "Banjir"
    magnitude: Optional[float] = None
    depth: Optional[str] = None
    location: str
    coordinates: List[float] = Field(..., min_length=2, max_length=2)  # [lat, lng]
    time: str
    risk_level: str = "Rendah"  # Rendah, Sedang, Tinggi


# ─── Risk Analysis ───────────────────────────────────────────────

class RiskAnalysisRequest(BaseModel):
    """Request body for risk analysis."""
    disaster_type: str
    magnitude: Optional[float] = None
    depth_km: Optional[float] = None
    latitude: float
    longitude: float


class RiskAnalysisResponse(BaseModel):
    """Response from risk analysis."""
    risk_level: str  # Rendah, Sedang, Tinggi
    confidence: float  # 0.0 - 1.0
    action: str  # Recommended action
    details: str  # Detailed explanation


# ─── Chat ────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    """A single chat message."""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""
    message: str
    disaster_context: Optional[DisasterInfo] = None
    history: Optional[List[ChatMessage]] = None


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""
    reply: str
    suggestions: Optional[List[str]] = None


# ─── Hoax Analysis ───────────────────────────────────────────────

class HoaxAnalysisRequest(BaseModel):
    """Request schema for hoax classification."""
    text: str


class HoaxAnalysisResponse(BaseModel):
    """Response schema for hoax classification."""
    is_hoax: bool
    label: str  # "Hoaks" or "Fakta"
    confidence: float
    details: str
    action: str


# ─── News ────────────────────────────────────────────────────────

class NewsItem(BaseModel):
    """Schema for a news article."""
    id: str
    title: str
    link: Optional[str] = None
    date: str
    category: str
    summary: Optional[str] = None

