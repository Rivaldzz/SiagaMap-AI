'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Calendar, MapPin, Activity, AlertTriangle, Layers, Info, Loader2, Brain } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Disaster {
  id: string;
  type: string;
  location: string;
  coordinates: [number, number];
  magnitude?: number;
  risk_level: string;
  time: string;
  depth?: string;
}

interface RiskAnalysis {
  risk_level: string;
  confidence: number;
  action: string;
  details: string;
}

interface DisasterDetailModalProps {
  disaster: Disaster | null;
  onClose: () => void;
}

export default function DisasterDetailModal({ disaster, onClose }: DisasterDetailModalProps) {
  const [analysis, setAnalysis] = useState<RiskAnalysis | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);

  useEffect(() => {
    if (!disaster) {
      setAnalysis(null);
      return;
    }

    const fetchAnalysis = async () => {
      setLoadingAnalysis(true);
      try {
        // Parse depth to numeric
        let depthKm: number | null = null;
        if (disaster.depth) {
          const match = disaster.depth.match(/[\d.]+/);
          if (match) depthKm = parseFloat(match[0]);
        }

        const response = await fetch(`${API_URL}/api/analyze-risk`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            disaster_type: disaster.type,
            magnitude: disaster.magnitude || null,
            depth_km: depthKm,
            latitude: disaster.coordinates[0],
            longitude: disaster.coordinates[1],
          }),
        });

        if (response.ok) {
          const data = await response.json();
          setAnalysis(data);
        }
      } catch (error) {
        console.error('Failed to fetch AI analysis:', error);
      } finally {
        setLoadingAnalysis(false);
      }
    };

    fetchAnalysis();
  }, [disaster]);

  if (!disaster) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[2000] flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
        />

        {/* ModalContent */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl overflow-hidden border border-white/20"
        >
          {/* Header */}
          <div className={`p-6 flex items-center justify-between ${
            disaster.risk_level === 'Tinggi' ? 'bg-red-50 to-white' :
            disaster.risk_level === 'Sedang' ? 'bg-amber-50 to-white' :
            'bg-blue-50 to-white'
          }`}>
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg ${
                disaster.risk_level === 'Tinggi' ? 'bg-red-500' :
                disaster.risk_level === 'Sedang' ? 'bg-amber-500' :
                'bg-blue-500'
              }`}>
                <AlertTriangle className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900">{disaster.type}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                    disaster.risk_level === 'Tinggi' ? 'bg-red-100 text-red-700' :
                    disaster.risk_level === 'Sedang' ? 'bg-amber-100 text-amber-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                    Risiko {disaster.risk_level}
                  </span>
                  <span className="text-[10px] font-medium text-slate-500">ID: {disaster.id}</span>
                </div>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-black/5 rounded-full transition-colors text-slate-500"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="p-8 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Location Information */}
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
                    <MapPin className="w-4 h-4 text-slate-500" />
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Lokasi Kejadian</p>
                    <p className="text-sm font-semibold text-slate-800 leading-tight">{disaster.location}</p>
                    <p className="text-xs text-slate-50 font-mono mt-1 px-1.5 py-0.5 bg-slate-800 rounded w-fit">
                      {disaster.coordinates[0].toFixed(4)}, {disaster.coordinates[1].toFixed(4)}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
                    <Calendar className="w-4 h-4 text-slate-500" />
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Waktu Kejadian</p>
                    <p className="text-sm font-semibold text-slate-800">{disaster.time}</p>
                  </div>
                </div>
              </div>

              {/* Technical Specifications */}
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
                    <Activity className="w-4 h-4 text-slate-500" />
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Kekuatan / Intensitas</p>
                    <p className="text-sm font-semibold text-slate-800">
                      {disaster.magnitude ? `${disaster.magnitude} SR` : 'Data Tidak Tersedia'}
                    </p>
                  </div>
                </div>

                {disaster.depth && (
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
                      <Layers className="w-4 h-4 text-slate-500" />
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Kedalaman</p>
                      <p className="text-sm font-semibold text-slate-800">{disaster.depth}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* AI Analysis Section */}
            <div className="p-4 bg-blue-50 border border-blue-100 rounded-2xl flex gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center shrink-0">
                {loadingAnalysis ? (
                  <Loader2 className="w-4 h-4 text-white animate-spin" />
                ) : (
                  <Brain className="w-4 h-4 text-white" />
                )}
              </div>
              <div className="space-y-1 flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-xs font-bold text-blue-700">Rekomendasi Mitigasi AI</p>
                  {analysis && (
                    <span className="text-[10px] font-bold px-1.5 py-0.5 bg-blue-200/50 text-blue-600 rounded-full">
                      Akurasi: {(analysis.confidence * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
                {loadingAnalysis ? (
                  <p className="text-xs text-blue-600/80 leading-relaxed">
                    Menganalisis parameter bencana dengan model AI...
                  </p>
                ) : analysis ? (
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-blue-700">{analysis.action}</p>
                    <p className="text-xs text-blue-600/80 leading-relaxed">{analysis.details}</p>
                  </div>
                ) : (
                  <p className="text-xs text-blue-600/80 leading-relaxed">
                    Tetap tenang dan ikuti arahan dari BPBD setempat. Pastikan jalur evakuasi bebas hambatan dan simpan dokumen penting dalam satu tas siap siaga.
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="px-8 py-6 bg-slate-50 border-t border-slate-100 flex justify-end">
            <button
              onClick={onClose}
              className="px-6 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-700 hover:bg-slate-100 transition-colors shadow-sm"
            >
              Tutup Rincian
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
