"""
Chat Engine — Knowledge-based AI chatbot for disaster mitigation guidance.

Uses TF-IDF vectorization + cosine similarity to find the most relevant
responses from a pre-built knowledge base of Indonesian disaster
mitigation protocols (BNPB guidelines).
"""

import logging
import re
from typing import List, Dict, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)

# ─── Knowledge Base ──────────────────────────────────────────────
# Structured as question-answer pairs covering Indonesian disaster
# mitigation protocols from BNPB (Badan Nasional Penanggulangan Bencana)

KNOWLEDGE_BASE = [
    # ── Gempa Bumi (Earthquake) ──
    {
        "keywords": "gempa bumi earthquake apa itu gempa seismik getaran",
        "topic": "Gempa Bumi — Penjelasan",
        "response": (
            "**Gempa bumi** adalah getaran yang terjadi di permukaan bumi akibat pelepasan energi "
            "dari dalam bumi secara tiba-tiba. Gempa bumi dapat disebabkan oleh:\n\n"
            "• **Tektonik** — pergerakan lempeng bumi\n"
            "• **Vulkanik** — aktivitas gunung berapi\n"
            "• **Runtuhan** — runtuhnya gua atau tambang\n\n"
            "Indonesia terletak di pertemuan 3 lempeng tektonik (Eurasia, Indo-Australia, Pasifik), "
            "sehingga sangat rawan gempa bumi."
        ),
    },
    {
        "keywords": "saat gempa terjadi gempa sedang gempa berlangsung ketika gempa bagaimana saat gempa",
        "topic": "Gempa Bumi — Saat Terjadi",
        "response": (
            "**Langkah saat gempa bumi terjadi:**\n\n"
            "🔴 **Di dalam gedung:**\n"
            "• Berlindung di bawah meja kokoh atau di samping furnitur besar\n"
            "• Lindungi kepala dengan bantal atau tangan\n"
            "• Jauhi kaca, jendela, dan benda yang bisa jatuh\n"
            "• JANGAN gunakan lift — gunakan tangga darurat\n\n"
            "🔴 **Di luar gedung:**\n"
            "• Jauhi bangunan, tiang listrik, dan pohon\n"
            "• Pergi ke area lapang yang aman\n"
            "• Jika di kendaraan, berhenti dan tetap di dalam kendaraan\n\n"
            "🔴 **Ingat prinsip: DROP — COVER — HOLD ON**"
        ),
    },
    {
        "keywords": "setelah gempa pasca gempa sesudah gempa selesai gempa berhenti",
        "topic": "Gempa Bumi — Pasca Kejadian",
        "response": (
            "**Langkah setelah gempa bumi:**\n\n"
            "1. Periksa diri sendiri dan orang sekitar — berikan P3K jika perlu\n"
            "2. Periksa kerusakan bangunan sebelum masuk kembali\n"
            "3. Waspadai **gempa susulan** (aftershock)\n"
            "4. Jauhi bangunan yang rusak atau retak\n"
            "5. Matikan kompor gas dan peralatan listrik\n"
            "6. Dengarkan informasi resmi dari BMKG dan BNPB\n"
            "7. Jangan menyebarkan berita bohong (hoaks)"
        ),
    },
    {
        "keywords": "persiapan gempa siaga gempa sebelum gempa tas siaga kesiapsiagaan",
        "topic": "Gempa Bumi — Kesiapsiagaan",
        "response": (
            "**Persiapan menghadapi gempa bumi:**\n\n"
            "📦 **Tas Siaga Bencana** harus berisi:\n"
            "• Air minum minimal 3 liter per orang\n"
            "• Makanan tahan lama (biskuit, mie instan)\n"
            "• Obat-obatan pribadi dan P3K\n"
            "• Senter dan baterai cadangan\n"
            "• Dokumen penting dalam plastik kedap air\n"
            "• Uang tunai secukupnya\n"
            "• Peluit untuk memberi sinyal\n\n"
            "🏠 **Di rumah:**\n"
            "• Kenali jalur evakuasi dan titik kumpul\n"
            "• Amankan furnitur berat agar tidak mudah jatuh\n"
            "• Latihan simulasi gempa bersama keluarga"
        ),
    },

    # ── Tsunami ──
    {
        "keywords": "tsunami gelombang pasang air laut naik pantai ombak besar",
        "topic": "Tsunami — Penjelasan & Mitigasi",
        "response": (
            "**Tsunami** adalah gelombang laut yang sangat besar akibat gempa bumi bawah laut, "
            "letusan gunung berapi, atau longsor bawah laut.\n\n"
            "⚠️ **Tanda-tanda tsunami:**\n"
            "• Gempa bumi kuat terasa di daerah pantai\n"
            "• Air laut surut tiba-tiba dan cepat\n"
            "• Terdengar suara gemuruh dari arah laut\n\n"
            "🚨 **Yang harus dilakukan:**\n"
            "1. Segera lari ke tempat tinggi (minimal 30 meter dari pantai)\n"
            "2. Jauhi pantai, sungai, dan daerah rendah\n"
            "3. Jangan menunggu peringatan resmi jika sudah melihat tanda\n"
            "4. Ikuti rambu jalur evakuasi tsunami\n"
            "5. Jangan kembali ke pantai sampai ada peringatan aman resmi"
        ),
    },

    # ── Banjir (Flood) ──
    {
        "keywords": "banjir genangan air hujan lebat banjir bandang waterlogging flood",
        "topic": "Banjir — Mitigasi & Evakuasi",
        "response": (
            "**Panduan mitigasi banjir:**\n\n"
            "🔵 **Sebelum banjir:**\n"
            "• Pindahkan barang berharga ke tempat tinggi\n"
            "• Siapkan tas siaga dan dokumen penting\n"
            "• Kenali lokasi pengungsian terdekat\n\n"
            "🔵 **Saat banjir:**\n"
            "• Matikan listrik jika air mulai memasuki rumah\n"
            "• Jangan berjalan di arus air yang deras (bahaya terseret)\n"
            "• Hindari daerah aliran sungai dan saluran air\n"
            "• Minta bantuan jika terjebak\n\n"
            "🔵 **Setelah banjir:**\n"
            "• Bersihkan rumah dan semprot disinfektan\n"
            "• Periksa instalasi listrik sebelum dinyalakan\n"
            "• Waspada penyakit pasca banjir (diare, leptospirosis)"
        ),
    },

    # ── Erupsi Gunung Api (Volcanic Eruption) ──
    {
        "keywords": "gunung api erupsi letusan vulkanik abu vulkanik lava lahar merapi sinabung semeru kelud anak krakatau",
        "topic": "Erupsi Gunung Api — Mitigasi",
        "response": (
            "**Panduan mitigasi erupsi gunung api:**\n\n"
            "🌋 **Sebelum erupsi (Status Siaga/Awas):**\n"
            "• Ikuti arahan PVMBG dan BPBD setempat\n"
            "• Siapkan masker dan kacamata pelindung\n"
            "• Siapkan jalur evakuasi dari zona bahaya\n\n"
            "🌋 **Saat erupsi:**\n"
            "• Segera evakuasi dari zona bahaya (radius sesuai arahan)\n"
            "• Gunakan masker untuk melindungi pernapasan dari abu vulkanik\n"
            "• Lindungi sumber air dari kontaminasi abu\n"
            "• Jauhi lembah dan sungai yang berpotensi dilalui lahar\n\n"
            "🌋 **Setelah erupsi:**\n"
            "• Bersihkan atap dari abu vulkanik (bisa menyebabkan atap runtuh)\n"
            "• Jangan mengemudi saat hujan abu tebal\n"
            "• Pantau status gunung dari PVMBG"
        ),
    },

    # ── Cuaca Ekstrem ──
    {
        "keywords": "cuaca ekstrem hujan lebat badai angin kencang puting beliung petir kilat cuaca buruk",
        "topic": "Cuaca Ekstrem — Kewaspadaan",
        "response": (
            "**Panduan menghadapi cuaca ekstrem:**\n\n"
            "⛈️ **Hujan lebat & badai:**\n"
            "• Hindari berdiri di bawah pohon besar\n"
            "• Jauhi tiang listrik dan benda logam\n"
            "• Matikan peralatan elektronik saat petir\n"
            "• Jangan berkendara jika jarak pandang sangat rendah\n\n"
            "🌪️ **Angin kencang / puting beliung:**\n"
            "• Masuk ke dalam bangunan kokoh\n"
            "• Jauhi jendela kaca\n"
            "• Amankan barang di luar rumah yang bisa terbang\n\n"
            "📱 Pantau peringatan dini cuaca dari BMKG melalui website atau aplikasi resmi."
        ),
    },

    # ── Tanah Longsor ──
    {
        "keywords": "tanah longsor longsor gerakan tanah tebing bukit lereng erosi",
        "topic": "Tanah Longsor — Mitigasi",
        "response": (
            "**Panduan mitigasi tanah longsor:**\n\n"
            "⛰️ **Tanda-tanda tanah longsor:**\n"
            "• Muncul retakan di tanah atau dinding\n"
            "• Pohon-pohon mulai miring\n"
            "• Air sumur tiba-tiba keruh\n"
            "• Suara gemuruh dari arah lereng\n\n"
            "⛰️ **Yang harus dilakukan:**\n"
            "• Segera evakuasi ke tempat yang aman\n"
            "• Jauhi lereng, tebing, dan daerah aliran sungai\n"
            "• Jangan membangun di lereng curam\n"
            "• Buat terasering dan tanam pohon penahan erosi"
        ),
    },

    # ── Kebakaran Hutan ──
    {
        "keywords": "kebakaran hutan lahan karhutla asap kabut api hutan pembakaran",
        "topic": "Kebakaran Hutan & Lahan",
        "response": (
            "**Panduan menghadapi kebakaran hutan dan lahan (karhutla):**\n\n"
            "🔥 **Pencegahan:**\n"
            "• Jangan membakar lahan untuk pembukaan ladang\n"
            "• Buat sekat bakar di sekitar area pemukiman\n"
            "• Laporkan titik api ke Damkar/BNPB\n\n"
            "🔥 **Saat terjadi:**\n"
            "• Gunakan masker N95 untuk melindungi dari asap\n"
            "• Tutup jendela dan pintu rumah\n"
            "• Siapkan air dan kain basah\n"
            "• Evakuasi jika api mendekati pemukiman\n\n"
            "🫁 **Dampak kesehatan:**\n"
            "• Asap karhutla mengandung partikel PM2.5 yang berbahaya\n"
            "• Kelompok rentan (anak, lansia, ibu hamil) harus berada di dalam ruangan"
        ),
    },

    # ── Gelombang Tinggi ──
    {
        "keywords": "gelombang tinggi ombak laut perairan nelayan pelayaran maritim",
        "topic": "Gelombang Tinggi — Peringatan Maritim",
        "response": (
            "**Panduan menghadapi gelombang tinggi:**\n\n"
            "🌊 **Untuk nelayan:**\n"
            "• Jangan melaut saat BMKG mengeluarkan peringatan gelombang tinggi\n"
            "• Pastikan kapal berlabuh dengan aman\n"
            "• Siapkan peralatan keselamatan (pelampung, radio komunikasi)\n\n"
            "🌊 **Untuk warga pesisir:**\n"
            "• Jauhi tepi pantai saat ada peringatan\n"
            "• Pindahkan barang-barang dari tepi pantai\n"
            "• Pantau informasi BMKG secara berkala"
        ),
    },

    # ── General / Kontak Darurat ──
    {
        "keywords": "kontak darurat nomor telepon hotline bantuan lapor hubungi",
        "topic": "Kontak Darurat Bencana Indonesia",
        "response": (
            "**Nomor kontak darurat bencana Indonesia:**\n\n"
            "📞 **BNPB (Badan Nasional Penanggulangan Bencana):** 117\n"
            "📞 **Basarnas (SAR):** 115\n"
            "📞 **PMI (Palang Merah Indonesia):** (021) 7992325\n"
            "📞 **Ambulans:** 118 / 119\n"
            "📞 **Polisi:** 110\n"
            "📞 **Pemadam Kebakaran:** 113\n"
            "📞 **PLN (gangguan listrik):** 123\n\n"
            "🌐 **Website resmi:**\n"
            "• BMKG: https://www.bmkg.go.id\n"
            "• BNPB: https://www.bnpb.go.id\n"
            "• PVMBG: https://vsi.esdm.go.id"
        ),
    },
    {
        "keywords": "apa itu siagamap ai tentang siagamap siaga map sistem pemantauan",
        "topic": "Tentang SiagaMap AI",
        "response": (
            "**SiagaMap AI** adalah platform pemantauan bencana real-time yang mengintegrasikan "
            "data BMKG dengan kecerdasan buatan untuk mitigasi bencana.\n\n"
            "🤖 **Fitur utama:**\n"
            "• Peta bencana real-time dari data BMKG\n"
            "• Analisis risiko menggunakan AI (Machine Learning)\n"
            "• Asisten AI untuk panduan mitigasi bencana\n"
            "• Filter dan pelacakan bencana berdasarkan jenis\n\n"
            "Dikembangkan untuk membantu masyarakat Indonesia dalam kesiapsiagaan bencana."
        ),
    },
    {
        "keywords": "mitigasi apa itu mitigasi pencegahan bencana pengurangan risiko",
        "topic": "Mitigasi Bencana — Penjelasan Umum",
        "response": (
            "**Mitigasi bencana** adalah serangkaian upaya untuk mengurangi risiko bencana, "
            "baik melalui pembangunan fisik maupun peningkatan kesadaran masyarakat.\n\n"
            "📋 **Jenis mitigasi:**\n"
            "• **Mitigasi struktural** — pembangunan tanggul, penahan longsor, breakwater\n"
            "• **Mitigasi non-struktural** — edukasi, peringatan dini, pemetaan risiko, regulasi\n\n"
            "🎯 **Tujuan:**\n"
            "• Mengurangi korban jiwa dan kerugian material\n"
            "• Meningkatkan kesiapsiagaan masyarakat\n"
            "• Mempercepat pemulihan pasca bencana"
        ),
    },
    {
        "keywords": "p3k pertolongan pertama cedera luka darurat medis kesehatan",
        "topic": "Pertolongan Pertama pada Bencana",
        "response": (
            "**Pertolongan pertama saat bencana:**\n\n"
            "🩹 **Langkah dasar:**\n"
            "1. Pastikan keamanan diri sendiri terlebih dahulu\n"
            "2. Periksa kesadaran korban (panggil dan tepuk bahu)\n"
            "3. Hubungi bantuan medis (118/119)\n"
            "4. Hentikan pendarahan dengan menekan luka menggunakan kain bersih\n"
            "5. Jangan memindahkan korban jika dicurigai cedera tulang belakang\n\n"
            "🩹 **Isi kotak P3K:**\n"
            "• Perban, kasa steril, plester\n"
            "• Antiseptik (betadine, alkohol 70%)\n"
            "• Gunting, pinset\n"
            "• Obat penghilang rasa sakit (parasetamol)\n"
            "• Sarung tangan medis"
        ),
    },
]


class ChatEngine:
    """TF-IDF based chatbot engine for disaster mitigation Q&A."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            max_features=5000,
            stop_words=None,  # Keep all Indonesian words
        )
        self.knowledge = KNOWLEDGE_BASE
        self._build_index()
        logger.info(f"Chat engine initialized with {len(self.knowledge)} knowledge entries")

    def _build_index(self):
        """Build TF-IDF index from knowledge base."""
        # Combine keywords + topic for better matching
        corpus = [
            f"{item['keywords']} {item['topic']} {item['response'][:200]}"
            for item in self.knowledge
        ]
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def _find_best_match(self, query: str, threshold: float = 0.05) -> Optional[Dict]:
        """Find the best matching knowledge entry for a query."""
        query_vec = self.vectorizer.transform([query.lower()])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]

        logger.debug(f"Query: '{query}' → Best match: {self.knowledge[best_idx]['topic']} (score: {best_score:.4f})")

        if best_score >= threshold:
            return {
                "entry": self.knowledge[best_idx],
                "score": float(best_score),
            }
        return None

    def _build_context_response(self, disaster_context: Optional[Dict]) -> str:
        """Build a contextual response based on selected disaster data."""
        if not disaster_context:
            return ""

        d_type = disaster_context.get("type", "Bencana")
        location = disaster_context.get("location", "")
        magnitude = disaster_context.get("magnitude")
        risk = disaster_context.get("risk_level", "Rendah")

        context = f"\n\n📍 **Konteks bencana terpilih:**\n"
        context += f"• Jenis: {d_type}\n"
        context += f"• Lokasi: {location}\n"
        if magnitude:
            context += f"• Magnitudo: {magnitude} SR\n"
        context += f"• Risiko: {risk}\n"

        return context

    def get_response(
        self,
        message: str,
        disaster_context: Optional[Dict] = None,
    ) -> Dict:
        """
        Generate a response for a user message.

        Returns:
            dict with 'reply' and 'suggestions'
        """
        # Clean up the message
        clean_msg = re.sub(r'[^\w\s]', ' ', message.lower()).strip()

        if not clean_msg:
            return {
                "reply": "Silakan ajukan pertanyaan tentang mitigasi bencana. Saya siap membantu! 🛡️",
                "suggestions": [
                    "Apa yang harus dilakukan saat gempa?",
                    "Bagaimana persiapan menghadapi tsunami?",
                    "Kontak darurat bencana",
                ],
            }

        # Greetings
        greetings = ["halo", "hai", "hello", "hi", "selamat", "assalamualaikum", "pagi", "siang", "sore", "malam"]
        if any(g in clean_msg.split() for g in greetings):
            ctx = self._build_context_response(disaster_context)
            return {
                "reply": (
                    f"Halo! 👋 Saya asisten **SiagaMap AI** yang siap membantu Anda "
                    f"dengan informasi mitigasi bencana.\n\n"
                    f"Anda bisa bertanya tentang:\n"
                    f"• 🌏 Gempa bumi, tsunami, banjir\n"
                    f"• 🌋 Erupsi gunung api\n"
                    f"• 📦 Persiapan tas siaga bencana\n"
                    f"• 📞 Nomor kontak darurat\n"
                    f"• 🩹 Pertolongan pertama{ctx}"
                ),
                "suggestions": [
                    "Apa yang harus dilakukan saat gempa bumi?",
                    "Bagaimana cara mempersiapkan tas siaga?",
                    "Apa tanda-tanda tsunami?",
                ],
            }

        # Terima kasih (Thank you)
        thanks = ["terima kasih", "makasih", "thanks", "thx"]
        if any(t in clean_msg for t in thanks):
            return {
                "reply": "Sama-sama! 😊 Jangan ragu bertanya lagi jika membutuhkan informasi lainnya. Tetap waspada dan siaga! 🛡️",
                "suggestions": [
                    "Kontak darurat bencana",
                    "Apa itu mitigasi bencana?",
                    "Pertolongan pertama saat bencana",
                ],
            }

        # Find best match from knowledge base
        match = self._find_best_match(clean_msg)

        # Context keywords related to disaster mitigation
        context_keywords = [
            "gempa", "tsunami", "banjir", "vulkanik", "gunung", "erupsi", 
            "longsor", "cuaca", "hujan", "angin", "petir", "maritim", "gelombang",
            "kebakaran", "hutan", "lahar", "mitigasi", "evakuasi", "bencana", 
            "bantuan", "darurat", "posko", "siaga", "luka", "p3k", "obat", "nomor",
            "kontak", "telefon", "sar", "bnpb", "bmkg", "pvmbg", "sistem", "siagamap", "peta"
        ]

        has_context_word = any(kw in clean_msg for kw in context_keywords)
        is_in_context = (match is not None and match["score"] >= 0.11) or has_context_word

        if not is_in_context:
            return {
                "reply": "Maaf, saya tidak bisa menjawab karena tidak sesuai konteks. Silakan ajukan pertanyaan seputar mitigasi bencana, pertolongan pertama, atau informasi kedaruratan.",
                "suggestions": [
                    "Apa yang harus dilakukan saat gempa?",
                    "Panduan mitigasi banjir",
                    "Kontak darurat bencana"
                ]
            }

        if match:
            entry = match["entry"]
            score = match["score"]
            ctx = self._build_context_response(disaster_context)

            reply = entry["response"] + ctx

            # Generate related suggestions
            suggestions = self._get_related_suggestions(entry["topic"], clean_msg)

            return {
                "reply": reply,
                "suggestions": suggestions,
            }

        # No match found — generic fallback
        ctx = self._build_context_response(disaster_context)
        return {
            "reply": (
                f"Terima kasih atas pertanyaan Anda. Saya akan berusaha membantu.\n\n"
                f"Untuk mendapatkan jawaban yang lebih akurat, coba gunakan kata kunci seperti: "
                f"**gempa**, **tsunami**, **banjir**, **erupsi**, **cuaca**, atau **evakuasi**.{ctx}\n\n"
                f"💡 Anda juga bisa bertanya: *\"Apa yang harus dilakukan saat gempa bumi?\"*"
            ),
            "suggestions": [
                "Apa yang harus dilakukan saat gempa?",
                "Panduan mitigasi banjir",
                "Kontak darurat bencana",
            ],
        }


    def _get_related_suggestions(self, current_topic: str, query: str) -> List[str]:
        """Generate related follow-up suggestions."""
        suggestion_map = {
            "Gempa Bumi": [
                "Apa yang harus dilakukan setelah gempa?",
                "Bagaimana persiapan menghadapi gempa?",
                "Apakah gempa bisa memicu tsunami?",
            ],
            "Tsunami": [
                "Apa yang harus dilakukan saat gempa di pantai?",
                "Kontak darurat bencana",
                "Pertolongan pertama saat bencana",
            ],
            "Banjir": [
                "Kontak darurat bencana",
                "Apa isi tas siaga bencana?",
                "Pertolongan pertama saat bencana",
            ],
            "Erupsi": [
                "Apa dampak abu vulkanik bagi kesehatan?",
                "Kontak darurat bencana",
                "Apa itu mitigasi bencana?",
            ],
            "Cuaca": [
                "Apa itu banjir bandang?",
                "Kontak darurat bencana",
                "Apa yang harus dilakukan saat tanah longsor?",
            ],
        }

        for key, suggestions in suggestion_map.items():
            if key.lower() in current_topic.lower():
                return suggestions

        return [
            "Apa itu mitigasi bencana?",
            "Kontak darurat bencana Indonesia",
            "Tentang SiagaMap AI",
        ]


# ─── Global Instance ────────────────────────────────────────────

_engine: Optional[ChatEngine] = None


def get_chat_engine() -> ChatEngine:
    """Get or create the global chat engine instance."""
    global _engine
    if _engine is None:
        _engine = ChatEngine()
    return _engine
