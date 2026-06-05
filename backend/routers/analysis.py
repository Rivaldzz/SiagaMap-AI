"""
Risk and Hoax Analysis Router — AI-powered hazard and verification models.
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
import logging
from PIL import Image
import io

from backend.schemas import RiskAnalysisRequest, RiskAnalysisResponse, HoaxAnalysisRequest, HoaxAnalysisResponse
from backend.models.risk_model import predict_risk
from backend.models.hoax_model import predict_hoax

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze-risk", response_model=RiskAnalysisResponse)
async def analyze_risk(request: RiskAnalysisRequest):
    """
    Analyze disaster risk level using the AI model.
    
    Takes disaster parameters and returns risk classification
    with confidence score and recommended action.
    """
    try:
        # Parse depth from string if needed
        depth_km = request.depth_km

        result = predict_risk(
            disaster_type=request.disaster_type,
            magnitude=request.magnitude,
            depth_km=depth_km,
            latitude=request.latitude,
            longitude=request.longitude,
        )

        return RiskAnalysisResponse(**result)

    except Exception as e:
        logger.error(f"Error analyzing risk: {e}")
        raise HTTPException(
            status_code=500,
            detail="Gagal menganalisis risiko bencana"
        )


@router.post("/analyze-hoax", response_model=HoaxAnalysisResponse)
async def analyze_hoax(request: HoaxAnalysisRequest):
    """
    Analyze text/news using AI to detect if it is a hoax or fact.
    """
    try:
        result = predict_hoax(request.text)
        return HoaxAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"Error analyzing hoax: {e}")
        raise HTTPException(
            status_code=500,
            detail="Gagal menganalisis informasi hoax"
        )


@router.post("/analyze-hoax-image", response_model=HoaxAnalysisResponse)
async def analyze_hoax_image(
    title: str = Form(...),
    image: UploadFile = File(...)
):
    """
    Analyze both a headline and an uploaded image for potential hoaxes.
    Uses PIL to scan for software traces in metadata and analyzes compression ratio.
    """
    try:
        # Read image bytes
        image_bytes = await image.read()
        
        # Try to parse with PIL
        is_modified = False
        is_excessively_compressed = False
        software_used = None
        
        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            
            # 1. Check metadata info dictionary
            info = pil_img.info
            for key, val in info.items():
                if isinstance(val, str) and any(sw in val.lower() for sw in ["photoshop", "gimp", "canva", "picsart", "pixlr", "snapseed", "lightroom"]):
                    is_modified = True
                    software_used = val
                    break
            
            # 2. Check EXIF metadata
            exif = pil_img.getexif()
            if exif and not is_modified:
                # tag 305 is Software
                if 305 in exif:
                    software = str(exif[305]).lower()
                    if any(sw in software for sw in ["photoshop", "gimp", "canva", "picsart", "pixlr", "snapseed", "lightroom"]):
                        is_modified = True
                        software_used = exif[305]
                        
            # 3. Check compression ratio (bits per pixel)
            width, height = pil_img.size
            pixels = width * height
            if pixels > 0:
                bpp = (len(image_bytes) * 8) / pixels
                # If BPP is extremely low (< 0.15), it implies excessive compression/social media screenshot
                is_excessively_compressed = bpp < 0.15
        except Exception as img_err:
            logger.warning(f"Could not analyze image bytes with PIL: {img_err}")
            
        # Analyze headline text
        text_result = predict_hoax(title)
        
        # Combine predictions
        base_prob = text_result["confidence"] if text_result["is_hoax"] else (1.0 - text_result["confidence"])
        
        # Boost hoax probability if image exhibits traces
        if is_modified:
            base_prob = min(0.98, base_prob + 0.35)
        elif is_excessively_compressed:
            base_prob = min(0.92, base_prob + 0.15)
            
        is_hoax = base_prob > 0.5
        confidence = base_prob if is_hoax else (1.0 - base_prob)
        
        # Generate detailed report
        image_insights = []
        if is_modified:
            image_insights.append(f"Terdeteksi jejak manipulasi digital menggunakan software ({software_used or 'Editing Tool'}) pada metadata EXIF.")
        if is_excessively_compressed:
            image_insights.append("Analisis piksel menunjukkan tingkat kompresi ekstrem (bpp rendah), mengindikasikan gambar hasil tangkapan layar (screenshot) berulang dari media sosial.")
        if not is_modified and not is_excessively_compressed:
            image_insights.append("Metadata gambar bersih dari jejak modifikasi software pengolah gambar populer.")
            
        label = "Hoaks" if is_hoax else "Fakta"
        
        details = (
            f"Hasil Analisis Gabungan AI:\n\n"
            f"• Analisis Gambar: {', '.join(image_insights)}\n\n"
            f"• Analisis Narasi: {text_result['details']}"
        )
        
        action = text_result["action"]
        if is_hoax and is_modified:
            action = "⚠️ Peringatan Keras: Gambar terbukti telah direkayasa secara digital! " + action
            
        return HoaxAnalysisResponse(
            is_hoax=is_hoax,
            label=label,
            confidence=round(confidence, 3),
            details=details,
            action=action
        )
        
    except Exception as e:
        logger.error(f"Error in analyze_hoax_image: {e}")
        raise HTTPException(
            status_code=500,
            detail="Gagal menganalisis berita bergambar"
        )


