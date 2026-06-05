"""
Chat Router — AI chatbot for disaster mitigation Q&A.
"""

from fastapi import APIRouter, HTTPException
import logging

from backend.schemas import ChatRequest, ChatResponse
from backend.models.chat_engine import get_chat_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the SiagaMap AI assistant.
    
    Accepts a user message and optional disaster context,
    returns mitigation guidance from the knowledge base.
    """
    try:
        engine = get_chat_engine()

        # Convert disaster context to dict if provided
        disaster_dict = None
        if request.disaster_context:
            disaster_dict = request.disaster_context.model_dump()

        result = engine.get_response(
            message=request.message,
            disaster_context=disaster_dict,
        )

        return ChatResponse(
            reply=result["reply"],
            suggestions=result.get("suggestions"),
        )

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(
            status_code=500,
            detail="Gagal memproses pesan chat"
        )
