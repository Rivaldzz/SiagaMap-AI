"""
Risk Classification Model — Uses scikit-learn RandomForestClassifier
to predict disaster risk levels based on earthquake parameters.

The model is trained on a curated synthetic dataset at startup
and predicts: Rendah (Low), Sedang (Medium), Tinggi (High).
"""

import numpy as np
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# ─── Global Model State ─────────────────────────────────────────

_model: Optional[RandomForestClassifier] = None
_label_encoder: Optional[LabelEncoder] = None
_type_encoder: Optional[LabelEncoder] = None

# ─── Disaster Type Mapping ───────────────────────────────────────

DISASTER_TYPES = [
    "Gempa Bumi",
    "Gempa Dirasakan",
    "Tsunami",
    "Erupsi Gunung Api",
    "Banjir",
    "Tanah Longsor",
    "Prakiraan Cuaca Ekstrem",
    "Kebakaran Hutan",
    "Gelombang Tinggi",
]

# ─── Training Data ───────────────────────────────────────────────
# Features: [type_encoded, magnitude, depth_km, abs_latitude, longitude]
# Labels:   Rendah, Sedang, Tinggi

def _generate_training_data() -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a curated training dataset based on BNPB (Badan Nasional
    Penanggulangan Bencana) risk classification guidelines.
    """
    samples = []
    labels = []

    # ── Gempa Bumi scenarios ──
    # Shallow + strong = Tinggi
    for mag in np.arange(6.5, 9.0, 0.3):
        for depth in np.arange(5, 35, 5):
            samples.append([0, mag, depth, -5.0 + np.random.uniform(-3, 3), 110 + np.random.uniform(-10, 20)])
            labels.append("Tinggi")

    # Moderate magnitude, moderate depth = Sedang
    for mag in np.arange(4.5, 6.5, 0.3):
        for depth in np.arange(10, 60, 8):
            samples.append([0, mag, depth, -3.0 + np.random.uniform(-5, 5), 115 + np.random.uniform(-15, 25)])
            labels.append("Sedang")

    # Low magnitude or deep = Rendah
    for mag in np.arange(2.0, 4.5, 0.3):
        for depth in np.arange(30, 200, 15):
            samples.append([0, mag, depth, -4.0 + np.random.uniform(-4, 4), 120 + np.random.uniform(-20, 20)])
            labels.append("Rendah")

    # Deep + strong can still be Sedang
    for mag in np.arange(5.5, 7.5, 0.3):
        for depth in np.arange(70, 300, 20):
            samples.append([0, mag, depth, -6.0 + np.random.uniform(-2, 2), 125 + np.random.uniform(-10, 10)])
            labels.append("Sedang")

    # ── Gempa Dirasakan (1) ──
    for mag in np.arange(3.0, 5.5, 0.3):
        for depth in np.arange(5, 25, 5):
            samples.append([1, mag, depth, -6.0 + np.random.uniform(-2, 3), 108 + np.random.uniform(-5, 15)])
            labels.append("Sedang")

    for mag in np.arange(2.0, 3.5, 0.3):
        for depth in np.arange(10, 50, 8):
            samples.append([1, mag, depth, -7.0 + np.random.uniform(-1, 2), 112 + np.random.uniform(-5, 10)])
            labels.append("Rendah")

    # ── Tsunami (2) ── always Tinggi
    for mag in np.arange(7.0, 9.5, 0.3):
        for depth in np.arange(5, 40, 5):
            samples.append([2, mag, depth, -5.0 + np.random.uniform(-3, 3), 105 + np.random.uniform(-10, 30)])
            labels.append("Tinggi")

    # ── Erupsi Gunung Api (3) ──
    for _ in range(30):
        samples.append([3, 0, 0, -7.5 + np.random.uniform(-1, 1), 110 + np.random.uniform(-2, 3)])
        labels.append("Tinggi")

    for _ in range(20):
        samples.append([3, 0, 0, -3.0 + np.random.uniform(-2, 2), 125 + np.random.uniform(-5, 5)])
        labels.append("Sedang")

    # ── Banjir (4) ──
    for _ in range(25):
        samples.append([4, 0, 0, -6.2 + np.random.uniform(-1, 1), 106.8 + np.random.uniform(-0.5, 0.5)])
        labels.append("Sedang")

    for _ in range(15):
        samples.append([4, 0, 0, -7.0 + np.random.uniform(-2, 2), 110 + np.random.uniform(-5, 5)])
        labels.append("Rendah")

    # ── Cuaca Ekstrem (6) ──
    for _ in range(20):
        samples.append([6, 0, 0, -5.0 + np.random.uniform(-3, 3), 115 + np.random.uniform(-15, 15)])
        labels.append("Rendah")

    for _ in range(15):
        samples.append([6, 0, 0, -6.0 + np.random.uniform(-1, 1), 106 + np.random.uniform(-1, 1)])
        labels.append("Sedang")

    return np.array(samples), np.array(labels)


def train_model():
    """Train the risk classification model at startup."""
    global _model, _label_encoder

    logger.info("Training risk classification model...")

    X, y = _generate_training_data()

    _label_encoder = LabelEncoder()
    y_encoded = _label_encoder.fit_transform(y)

    _model = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1,
    )
    _model.fit(X, y_encoded)

    # Log training accuracy
    train_accuracy = _model.score(X, y_encoded)
    logger.info(f"Model trained. Training accuracy: {train_accuracy:.2%}")
    logger.info(f"Classes: {list(_label_encoder.classes_)}")


def predict_risk(
    disaster_type: str,
    magnitude: Optional[float] = None,
    depth_km: Optional[float] = None,
    latitude: float = -2.5,
    longitude: float = 118.0,
) -> Dict:
    """
    Predict risk level for a disaster event.

    Returns:
        dict with 'risk_level', 'confidence', 'action', 'details'
    """
    global _model, _label_encoder

    if _model is None or _label_encoder is None:
        train_model()

    # Encode disaster type
    type_index = 0
    for i, dt in enumerate(DISASTER_TYPES):
        if dt.lower() in disaster_type.lower() or disaster_type.lower() in dt.lower():
            type_index = i
            break

    # Prepare features
    mag = magnitude if magnitude is not None else 0.0
    depth = depth_km if depth_km is not None else 0.0

    features = np.array([[type_index, mag, depth, latitude, longitude]])

    # Predict
    prediction = _model.predict(features)[0]
    probabilities = _model.predict_proba(features)[0]
    confidence = float(np.max(probabilities))

    risk_level = _label_encoder.inverse_transform([prediction])[0]

    # Generate action based on risk level
    actions = {
        "Tinggi": "Segera Evakuasi — Ikuti jalur evakuasi terdekat dan jauhi area berbahaya.",
        "Sedang": "Waspada & Siaga — Pantau informasi terkini dari BMKG dan siapkan tas siaga bencana.",
        "Rendah": "Tetap Tenang — Tidak perlu panik, tetap waspada dan ikuti arahan petugas.",
    }

    # Generate detailed explanation
    details_map = {
        "Tinggi": (
            f"Analisis AI mendeteksi risiko TINGGI berdasarkan parameter: "
            f"Tipe={disaster_type}, Magnitudo={mag:.1f} SR, Kedalaman={depth:.0f} km. "
            f"Tingkat kepercayaan model: {confidence:.0%}. "
            f"Segera lakukan evakuasi dan ikuti protokol darurat BNPB."
        ),
        "Sedang": (
            f"Analisis AI menunjukkan risiko SEDANG. "
            f"Parameter: Tipe={disaster_type}, Magnitudo={mag:.1f} SR, Kedalaman={depth:.0f} km. "
            f"Kepercayaan: {confidence:.0%}. "
            f"Siapkan perlengkapan darurat dan pantau perkembangan dari BMKG."
        ),
        "Rendah": (
            f"Analisis AI menunjukkan risiko RENDAH. "
            f"Parameter: Tipe={disaster_type}, Magnitudo={mag:.1f} SR, Kedalaman={depth:.0f} km. "
            f"Kepercayaan: {confidence:.0%}. "
            f"Tidak ada ancaman signifikan, tetap waspada terhadap informasi terbaru."
        ),
    }

    return {
        "risk_level": risk_level,
        "confidence": round(confidence, 3),
        "action": actions.get(risk_level, "Pantau situasi terkini."),
        "details": details_map.get(risk_level, "Analisis tidak tersedia."),
    }
