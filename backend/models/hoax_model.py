"""
Hoax Detection Model — Uses scikit-learn TF-IDF + Logistic Regression
to classify disaster-related information as Hoax (Hoaks) or Fact (Fakta).

The model is trained on a dataset of Indonesian disaster rumors,
fake warnings, and official BMKG/BNPB releases.
"""

import numpy as np
import logging
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# ─── Global Model State ─────────────────────────────────────────

_hoax_model: Optional[Pipeline] = None

# ─── Training Dataset ────────────────────────────────────────────

HOAX_DATA = [
    # ── Hoaxes / Rumors (Label: 1) ──
    ("Akan terjadi gempa susulan dahsyat berkekuatan 8.5 SR di Jakarta malam ini pukul 23.00, bersiap evakuasi.", 1),
    ("BMKG mengeluarkan peringatan gempa megathrust akan menenggelamkan pulau Jawa besok pagi.", 1),
    ("Air laut di Pantai Ancol surut mendadak sampai 20 meter, dipastikan tsunami besar segera menyusul.", 1),
    ("Berdasarkan ramalan paranormal, gempa besar magnitudo 9.0 akan menghancurkan Yogyakarta minggu depan.", 1),
    ("Lava pijar Gunung Merapi telah mengalir sejauh 30 km hingga mencapai pusat kota Yogyakarta.", 1),
    ("Peringatan dini tsunami dikeluarkan untuk seluruh wilayah Selat Sunda akibat gempa magnitudo 3.2.", 1),
    ("Badai angin tornado raksasa setinggi 100 meter akan menyapu bersih kota Surabaya besok sore.", 1),
    ("Jangan keluar rumah selama 3 hari karena gas beracun mematikan dari letusan gunung berapi menyebar di seluruh Indonesia.", 1),
    ("Pemerintah menyembunyikan data gempa bumi 10 SR agar masyarakat tidak panik.", 1),
    ("Foto satelit menunjukkan celah raksasa membelah pulau Sumatera menjadi dua bagian akibat gempa.", 1),
    ("Aliran listrik di seluruh Jawa Barat akan dimatikan total selama 1 bulan karena banjir bandang.", 1),
    ("Gempa susulan akan menghancurkan Cianjur malam ini, segera kosongkan rumah Anda sekarang juga!", 1),
    ("Tsunami setinggi 15 meter sedang mengarah ke Bali akibat gempa bumi di Kupang.", 1),
    ("Pernyataan resmi BMKG: Jakarta akan tenggelam akibat mencairnya es kutub utara secara instan sore nanti.", 1),
    ("Tingkat radiasi vulkanik mematikan menyelimuti Bandung akibat aktivitas tersembunyi gunung Tangkuban Parahu.", 1),
    ("Informasi A1: Alat pendeteksi gempa BMKG rusak total dan tidak bisa mendeteksi bencana lagi.", 1),
    ("Peringatan badai matahari akan memicu letusan serentak seluruh gunung api di Indonesia.", 1),
    ("Video viral ombak raksasa setinggi gedung menghantam pantai selatan Jawa tadi pagi.", 1),

    # ── Facts / Official News (Label: 0) ──
    ("BMKG menyatakan gempa bumi Magnitudo 5.2 di Sukabumi tidak berpotensi tsunami.", 0),
    ("Pusat Vulkanologi dan Mitigasi Bencana Geologi (PVMBG) menaikkan status Gunung Merapi menjadi Siaga (Level III).", 0),
    ("Banjir menggenangi sejumlah titik di wilayah Jakarta Selatan dengan ketinggian air 30-50 cm akibat curah hujan tinggi.", 0),
    ("Prakiraan cuaca BMKG hari ini: potensi hujan lebat disertai petir dan angin kencang di sebagian wilayah Jawa Barat.", 0),
    ("BNPB mendistribusikan tenda pengungsian dan bahan makanan untuk korban terdampak gempa bumi di Cianjur.", 0),
    ("BPBD DKI Jakarta mengimbau warga di bantaran sungai Ciliwung waspada terhadap kenaikan debit air di Pintu Air Manggarai.", 0),
    ("Masyarakat diimbau tetap tenang dan tidak terpengaruh oleh isu gempa susulan yang tidak dapat dipertanggungjawabkan.", 0),
    ("Gempa bumi tektonik Magnitudo 4.8 mengguncang wilayah Banda Neira, dirasakan nyata di dalam rumah.", 0),
    ("BMKG merilis peta prakiraan wilayah potensi banjir untuk bulan Juni sebagai langkah kesiapsiagaan.", 0),
    ("PVMBG melaporkan aktivitas vulkanik Gunung Anak Krakatau mengalami penurunan frekuensi embusan asap.", 0),
    ("Petugas Damkar dan BPBD berhasil mengevakuasi warga yang terjebak banjir di pemukiman padat Kelurahan Kampung Melayu.", 0),
    ("BMKG mengimbau operator pelayaran untuk mewaspadai potensi gelombang tinggi di perairan Samudra Hindia.", 0),
    ("Sistem peringatan dini (TEWS) BMKG mengirimkan notifikasi resmi gempa bumi Magnitudo 6.0 di laut barat Sumatera.", 0),
    ("Pos Pengamatan Gunung Api Semeru mencatat terjadinya guguran lava pijar dengan jarak luncur 1.500 meter.", 0),
    ("BNPB menyelenggarakan simulasi evakuasi mandiri bencana gempa dan tsunami di sekolah-sekolah pesisir.", 0),
    ("Kepala BMKG menegaskan hingga saat ini belum ada teknologi yang mampu memprediksi waktu terjadinya gempa secara pasti.", 0),
    ("Hujan dengan intensitas sedang memicu tanah longsor kecil yang sempat menutup jalan desa di daerah Sumedang.", 0),
    ("BMKG memperbarui data iklim bulanan dan memperkirakan musim kemarau akan datang lebih lambat tahun ini.", 0)
]


def _clean_text(text: str) -> str:
    """Preprocess text by lowercasing and removing punctuation/special chars."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def train_hoax_model():
    """Train the hoax detection classifier model."""
    global _hoax_model

    logger.info("Training hoax detection model...")

    # Prepare features and labels
    X = [t[0] for t in HOAX_DATA]
    y = [t[1] for t in HOAX_DATA]

    # Preprocess corpus
    X_cleaned = [_clean_text(text) for text in X]

    # Create scikit-learn pipeline
    pipeline = Pipeline([
        ('vectorizer', TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            max_features=1000,
            token_pattern=r'\b\w+\b'
        )),
        ('classifier', LogisticRegression(C=1.0, random_state=42))
    ])

    pipeline.fit(X_cleaned, y)
    logger.info("✅ Hoax detection model trained successfully.")
    _hoax_model = pipeline


def predict_hoax(text: str) -> Dict:
    """
    Analyze text to determine if it is a Hoax or a Fact.
    
    Returns:
        Dict containing label, confidence, details, and recommendations.
    """
    global _hoax_model

    if _hoax_model is None:
        train_hoax_model()

    cleaned = _clean_text(text)
    
    # Predict probabilities
    probs = _hoax_model.predict_proba([cleaned])[0]
    hoax_prob = probs[1]
    fact_prob = probs[0]
    
    # Determine label
    is_hoax = hoax_prob > 0.5
    confidence = float(hoax_prob if is_hoax else fact_prob)

    # Standard rules based on suspicious keywords/phrases to adjust prediction
    suspicious_patterns = [
        (r"ramalan|paranormal|dukun|meramal|prediksi tanggal|pukul", "adanya klaim prediksi gempa secara spesifik waktu/tanggal yang secara ilmiah tidak mungkin diprediksi mendahului"),
        (r"megathrust.*tenggelam|tenggelamkan pulau", "adanya klaim berlebihan (hiperbola) tentang kepunahan atau pulau tenggelam secara seketika"),
        (r"sembunyikan data|pemerintah.*bohong", "narasi konspirasi yang mencoba mendelegitimasi institusi resmi"),
        (r"hancur.*malam ini|hancurkan.*sekarang", "nada bahasa yang memicu kepanikan berlebih (fear mongering) tanpa didukung rilis resmi"),
        (r"viralkan|sebar.*sebelum terhapus|bagikan info ini", "instruksi viralitas paksa yang merupakan ciri khas berita bohong"),
    ]

    matched_reasons = []
    for pattern, reason in suspicious_patterns:
        if re.search(pattern, cleaned):
            matched_reasons.append(reason)
            # Boost hoax probability if suspicious keywords are found
            if not is_hoax:
                is_hoax = True
                confidence = min(0.85, confidence + 0.2)
            else:
                confidence = min(0.98, confidence + 0.1)

    label = "Hoaks" if is_hoax else "Fakta"

    # Generate details
    if is_hoax:
        if matched_reasons:
            reasons_str = " dan ".join(matched_reasons)
            details = (
                f"Analisis AI mendeteksi pesan ini berpotensi HOAKS. Faktor indikasi kuat mencakup {reasons_str}. "
                "Hingga saat ini, belum ada teknologi ilmiah yang dapat memprediksi gempa bumi secara spesifik tanggal dan jam."
            )
        else:
            details = (
                "Pesan ini diklasifikasikan sebagai HOAKS karena menggunakan diksi tidak resmi, "
                "menciptakan kepanikan (fear-mongering), atau tidak memiliki referensi ilmiah/sumber kredibel."
            )
        action = "Hindari menyebarkan berita ini. Cek berkala aplikasi resmi Info BMKG atau hubungi BPBD setempat."
    else:
        details = (
            "Informasi ini terdeteksi sebagai FAKTA / BERITA RESMI. Pola kalimat selaras dengan rilis pers resmi, "
            "menggunakan istilah teknis yang objektif (skala MMI, magnitudo, parameter gempa), "
            "dan bersumber dari otoritas kebencanaan (BMKG, PVMBG, BNPB)."
        )
        action = "Informasi ini valid. Tetap waspada, ikuti panduan mitigasi resmi, dan pantau perkembangan info."

    return {
        "is_hoax": is_hoax,
        "label": label,
        "confidence": round(confidence, 3),
        "details": details,
        "action": action
    }
