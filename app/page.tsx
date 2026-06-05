'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Shield, Map as MapIcon, BarChart3, Activity, AlertCircle, Filter, 
  ChevronRight, Newspaper, AlertTriangle, CheckCircle, Search, RefreshCw, Send, CheckCircle2, ShieldAlert, Loader2
} from 'lucide-react';
import AiAssistant from '@/components/AiAssistant';
import BmkgNews from '@/components/BmkgNews';
import DisasterDetailModal from '@/components/DisasterDetailModal';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, LineChart, Line, CartesianGrid, Legend 
} from 'recharts';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Dynamically import Map component to avoid SSR issues
const MapDisplay = dynamic(() => import('@/components/MapDisplay'), { 
  ssr: false,
  loading: () => <div className="w-full h-full min-h-[500px] bg-slate-100 dark:bg-slate-900 animate-pulse rounded-2xl flex items-center justify-center text-slate-500">Memuat Peta...</div>
});

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

interface HoaxResult {
  is_hoax: boolean;
  label: string;
  confidence: number;
  details: string;
  action: string;
}

export default function SiagaMapPage() {
  const [disasters, setDisasters] = useState<Disaster[]>([]);
  const [selectedDisaster, setSelectedDisaster] = useState<Disaster | null>(null);
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [activeFilters, setActiveFilters] = useState<string[]>([]);
  
  // Navigation tab: 'map' | 'news' | 'analytics'
  const [activeTab, setActiveTab] = useState<'map' | 'news' | 'analytics'>('map');
  
  // Hoax analysis state
  const [hoaxText, setHoaxText] = useState('');
  const [hoaxLoading, setHoaxLoading] = useState(false);
  const [hoaxResult, setHoaxResult] = useState<HoaxResult | null>(null);
  const [newsSearch, setNewsSearch] = useState('');

  // Image Hoax states
  const [isImageModalOpen, setIsImageModalOpen] = useState(false);
  const [imageModalTitle, setImageModalTitle] = useState('');
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageHoaxLoading, setImageHoaxLoading] = useState(false);
  const [imageHoaxResult, setImageHoaxResult] = useState<HoaxResult | null>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedImage(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleVerifyImageHoax = async () => {
    if (!imageModalTitle.trim() || !selectedImage) return;
    
    setImageHoaxLoading(true);
    setImageHoaxResult(null);
    
    const formData = new FormData();
    formData.append('title', imageModalTitle.trim());
    formData.append('image', selectedImage);
    
    try {
      const res = await fetch(`${API_URL}/api/analyze-hoax-image`, {
        method: 'POST',
        body: formData,
      });
      
      if (res.ok) {
        const data = await res.json();
        setImageHoaxResult(data);
      } else {
        throw new Error("Gagal memproses gambar dan teks.");
      }
    } catch (e) {
      console.error(e);
      setImageHoaxResult({
        is_hoax: true,
        label: "Gagal Analisis",
        confidence: 1.0,
        details: "Gagal menghubungkan ke server AI. Pastikan server backend Anda menyala.",
        action: "Silakan coba lagi nanti."
      });
    } finally {
      setImageHoaxLoading(false);
    }
  };


  const fetchDisasters = async () => {
    try {
      const res = await fetch(`${API_URL}/api/disasters`);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      setDisasters(data);
    } catch (error) {
      console.error("Failed to fetch disaster data", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Fetch system data
    fetchDisasters();
    
    // Request geolocation
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation([position.coords.latitude, position.coords.longitude]);
          setLocationError(null);
        },
        (error) => {
          console.warn("Geolocation denied or error:", error.message);
          setLocationError(error.code === 1 ? "Izin lokasi ditolak. Peta menggunakan pusat default." : "Gagal mengambil lokasi.");
        }
      );
    } else {
      setTimeout(() => setLocationError("Browser tidak mendukung geolocation."), 0);
    }
    
    // Set up polling every 15 seconds
    const interval = setInterval(fetchDisasters, 15000);
    
    const timer = setTimeout(() => {
      setMounted(true);
    }, 100);
    
    return () => {
      clearInterval(interval);
      clearTimeout(timer);
    };
  }, []);

  const availableTypes = Array.from(new Set(disasters.map(d => d.type)));

  const toggleFilter = (type: string) => {
    setActiveFilters(prev => 
      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
    );
  };

  const filteredDisasters = activeFilters.length > 0
    ? disasters.filter(d => activeFilters.includes(d.type))
    : disasters;

  // ─── Chart Data Pre-computation ─────────────────────────────────
  
  // 1. Disaster Types distribution (Bar Chart)
  const disasterTypeDistribution = disasters.reduce((acc: Record<string, number>, curr) => {
    acc[curr.type] = (acc[curr.type] || 0) + 1;
    return acc;
  }, {});
  
  const barChartData = Object.keys(disasterTypeDistribution).map(type => ({
    name: type,
    Jumlah: disasterTypeDistribution[type]
  }));

  // 2. Risk Level distribution (Pie Chart)
  const riskDistribution = disasters.reduce((acc: Record<string, number>, curr) => {
    acc[curr.risk_level] = (acc[curr.risk_level] || 0) + 1;
    return acc;
  }, { Rendah: 0, Sedang: 0, Tinggi: 0 });

  const pieChartData = [
    { name: 'Rendah', value: riskDistribution.Rendah, color: '#10b981' }, // Green
    { name: 'Sedang', value: riskDistribution.Sedang, color: '#f59e0b' }, // Amber
    { name: 'Tinggi', value: riskDistribution.Tinggi, color: '#ef4444' }  // Red
  ].filter(item => item.value > 0);

  // 3. Magnitude trends for earthquakes (Line Chart)
  const earthquakeTrends = disasters
    .filter(d => d.type.toLowerCase().includes('gempa') && d.magnitude && d.magnitude > 0)
    .slice(0, 10)
    .reverse()
    .map(d => ({
      tanggal: d.time.split(' ')[0] || 'Terkini',
      Magnitudo: d.magnitude,
      lokasi: d.location.split(' ').slice(-1)[0]
    }));

  const handleVerifyHoax = async (textToVerify?: string) => {
    const targetText = textToVerify || hoaxText.trim();
    if (!targetText) return;
    
    if (textToVerify) {
      setHoaxText(textToVerify);
    }
    
    setHoaxLoading(true);
    setHoaxResult(null);
    try {
      const response = await fetch(`${API_URL}/api/analyze-hoax`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: targetText })
      });
      if (response.ok) {
        const data = await response.json();
        setHoaxResult(data);
      } else {
        throw new Error("Gagal menganalisis teks");
      }
    } catch (e) {
      console.error(e);
      setHoaxResult({
        is_hoax: true,
        label: "Gagal Analisis",
        confidence: 1.0,
        details: "Koneksi terputus. Pastikan server backend berjalan pada port 8000.",
        action: "Cek koneksi internet Anda."
      });
    } finally {
      setHoaxLoading(false);
    }
  };

  return (
    <main className="relative min-h-screen flex flex-col font-sans text-slate-800 bg-slate-50">
      <div className="motif-watermark pointer-events-none opacity-20" />
      
      {/* Top Navigation Bar */}
      <header className="h-16 flex items-center justify-between px-6 bg-white/75 backdrop-blur-xl border-b border-slate-200/60 shadow-sm z-30 sticky top-0">
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-3"
        >
          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-slate-900 leading-none mb-1">SiagaMap <span className="text-blue-600">AI</span></h1>
            <p className="text-[9px] uppercase tracking-widest font-bold text-slate-500">Sistem Deteksi Hoaks & Analitik Bencana</p>
          </div>
        </motion.div>

        {/* Dynamic Tab Selector */}
        <div className="hidden md:flex bg-slate-100/80 p-1 rounded-xl border border-slate-200/50">
          <button
            onClick={() => setActiveTab('map')}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'map' 
                ? 'bg-white text-blue-600 shadow-sm' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <MapIcon className="w-3.5 h-3.5" /> Peta Bencana
          </button>
          <button
            onClick={() => setActiveTab('news')}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'news' 
                ? 'bg-white text-blue-600 shadow-sm' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Newspaper className="w-3.5 h-3.5" /> Berita & Cek Hoaks
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'analytics' 
                ? 'bg-white text-blue-600 shadow-sm' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" /> Analisis & Statistik
          </button>
        </div>

        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-4"
        >
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse"></span>
            <span className="text-xs font-semibold text-slate-600 hidden sm:inline">BMKG RSS Active</span>
          </div>
          <div className="h-6 w-px bg-slate-200 hidden sm:block"></div>
          <div className="text-right hidden sm:block">
            {mounted && (
              <>
                <div className="text-xs font-bold">{new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })} WIB</div>
                <div className="text-[9px] text-slate-500 font-semibold">{new Date().toLocaleDateString('id-ID', { day: '2-digit', month: 'long', year: 'numeric' })}</div>
              </>
            )}
          </div>
        </motion.div>
      </header>

      {/* Tab Navigation for Mobile */}
      <div className="flex md:hidden bg-slate-100 border-b border-slate-200 p-1.5 justify-around sticky top-16 z-20">
        <button
          onClick={() => setActiveTab('map')}
          className={`flex-1 flex flex-col items-center py-1 rounded-lg text-[10px] font-bold ${
            activeTab === 'map' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500'
          }`}
        >
          <MapIcon className="w-4 h-4 mb-0.5" /> Peta
        </button>
        <button
          onClick={() => setActiveTab('news')}
          className={`flex-1 flex flex-col items-center py-1 rounded-lg text-[10px] font-bold ${
            activeTab === 'news' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500'
          }`}
        >
          <Newspaper className="w-4 h-4 mb-0.5" /> Berita & Hoaks
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={`flex-1 flex flex-col items-center py-1 rounded-lg text-[10px] font-bold ${
            activeTab === 'analytics' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500'
          }`}
        >
          <BarChart3 className="w-4 h-4 mb-0.5" /> Statistik
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-4 grid grid-cols-1 lg:grid-cols-12 gap-4 relative z-10 max-w-[1600px] mx-auto w-full overflow-hidden">
        
        {/* Left Column: Swappable Tab Content */}
        <section className={`${activeTab === 'analytics' ? 'lg:col-span-12' : 'lg:col-span-8'} flex flex-col gap-4 relative min-h-[500px]`}>
          
          <AnimatePresence mode="wait">
            
            {/* TAB 1: INTERACTIVE MAP */}
            {activeTab === 'map' && (
              <motion.div 
                key="map-tab"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="flex-1 flex flex-col gap-4"
              >
                <div className="flex-1 relative rounded-3xl border border-slate-200 bg-white shadow-lg overflow-hidden min-h-[500px]">
                  
                  {/* Filter Overlay */}
                  <div className="absolute top-4 right-4 z-[1000]">
                    <div className="bg-white/90 backdrop-blur-md rounded-2xl shadow-xl border border-slate-200/80 p-3 flex flex-col gap-2 max-w-[200px]">
                      <div className="flex items-center gap-2 pb-1.5 border-b border-slate-100 text-slate-500">
                        <Filter className="w-3.5 h-3.5 text-blue-600" />
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-700">Filter Bencana</span>
                      </div>
                      <div className="flex flex-col gap-1 max-h-[180px] overflow-y-auto pr-1 scrollbar-thin">
                        {availableTypes.map(type => (
                          <button
                            key={type}
                            onClick={() => toggleFilter(type)}
                            className={`px-2 py-1.5 rounded-lg text-[10px] font-bold text-left transition-colors flex items-center justify-between gap-2 ${
                              activeFilters.length === 0 || activeFilters.includes(type)
                                ? 'bg-blue-50 text-blue-700'
                                : 'bg-transparent text-slate-500 hover:bg-slate-100'
                            }`}
                          >
                            <span className="truncate">{type}</span>
                            <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                              activeFilters.length === 0 || activeFilters.includes(type)
                                ? 'bg-blue-600' 
                                : 'bg-slate-300'
                            }`} />
                          </button>
                        ))}
                        {activeFilters.length > 0 && (
                          <button 
                            onClick={() => setActiveFilters([])}
                            className="px-2 py-1 mt-1 text-[9px] font-bold text-blue-500 hover:text-blue-700 uppercase text-center transition-colors border-t border-slate-100 pt-1.5"
                          >
                            Tampilkan Semua
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  <MapDisplay 
                    disasters={filteredDisasters} 
                    onSelectDisaster={setSelectedDisaster} 
                    userLocation={userLocation}
                  />
                  
                  {locationError && (
                    <motion.div 
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="absolute top-4 left-4 z-20 bg-amber-50/90 backdrop-blur-md border border-amber-200/80 px-3 py-1.5 rounded-xl flex items-center gap-2 shadow-sm"
                    >
                      <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                      <span className="text-[9px] font-bold text-amber-700 uppercase tracking-wider">{locationError}</span>
                    </motion.div>
                  )}
                  
                  {/* Risk Analysis Badge (Floating) */}
                  <AnimatePresence>
                    {selectedDisaster && (
                      <motion.div 
                        initial={{ opacity: 0, scale: 0.95, y: 15 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 15 }}
                        className="absolute bottom-4 left-4 right-4 sm:right-auto z-20"
                      >
                        <div className="bg-white/95 backdrop-blur-md border border-slate-200 p-1.5 rounded-2xl shadow-2xl flex items-center justify-between gap-4 max-w-sm sm:max-w-md">
                          <div className="flex items-center gap-3 p-2">
                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-lg ${
                              selectedDisaster.risk_level === 'Tinggi' ? 'bg-red-500 text-white shadow-red-200' :
                              selectedDisaster.risk_level === 'Sedang' ? 'bg-amber-500 text-white shadow-amber-200' :
                              'bg-emerald-500 text-white shadow-emerald-200'
                            }`}>
                              <AlertCircle className="w-5 h-5" />
                            </div>
                            <div className="min-w-0">
                              <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest leading-none mb-1">Indeks Risiko AI</p>
                              <p className="text-xs font-bold text-slate-800 truncate mb-0.5">{selectedDisaster.type} - {selectedDisaster.location}</p>
                              <p className={`text-[10px] font-black tracking-tight leading-none ${
                                selectedDisaster.risk_level === 'Tinggi' ? 'text-red-600' :
                                selectedDisaster.risk_level === 'Sedang' ? 'text-amber-600' :
                                'text-emerald-600'
                              }`}>
                                STATUS: SIAGA {selectedDisaster.risk_level.toUpperCase()}
                              </p>
                            </div>
                          </div>
                          
                          <button 
                            onClick={() => setSelectedDisaster({ ...selectedDisaster })} 
                            className="h-11 px-3 bg-slate-900 text-white rounded-xl flex items-center gap-1.5 hover:bg-slate-800 transition-all font-bold text-[10px] shrink-0"
                          >
                            Rincian <ChevronRight className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Mini Stats Bar */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col justify-center">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Bencana Terdeteksi</span>
                    <span className="text-2xl font-black text-slate-900 flex items-baseline gap-1.5">
                      {disasters.length} <span className="text-xs font-bold text-slate-500">Aktif</span>
                    </span>
                  </div>
                  <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col justify-center border-l-4 border-l-red-500">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Zona Risiko Tinggi</span>
                    <span className="text-2xl font-black text-red-600 flex items-baseline gap-1.5">
                      {disasters.filter(d => d.risk_level === 'Tinggi').length} <span className="text-xs font-bold text-slate-500">Lokasi</span>
                    </span>
                  </div>
                  <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col justify-center border-l-4 border-l-amber-500">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Zona Risiko Sedang</span>
                    <span className="text-2xl font-black text-amber-500 flex items-baseline gap-1.5">
                      {disasters.filter(d => d.risk_level === 'Sedang').length} <span className="text-xs font-bold text-slate-500">Lokasi</span>
                    </span>
                  </div>
                </div>
              </motion.div>
            )}

            {/* TAB 2: NEWS & HOAX BUSTER */}
            {activeTab === 'news' && (
              <motion.div 
                key="news-tab"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="flex-1 flex flex-col gap-4"
              >
                {/* Hoax Verification Panel */}
                <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-3xl p-6 shadow-xl relative overflow-hidden">
                  <div className="absolute right-0 bottom-0 translate-x-1/4 translate-y-1/4 opacity-10 pointer-events-none">
                    <ShieldAlert className="w-64 h-64" />
                  </div>
                  <div className="relative z-10">
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
                          <ShieldAlert className="w-5 h-5 text-white animate-pulse" />
                        </div>
                        <h3 className="font-bold text-base">Cek Hoaks Bencana AI</h3>
                      </div>
                      
                      <button
                        onClick={() => {
                          setIsImageModalOpen(true);
                          setImageHoaxResult(null);
                          setImageModalTitle('');
                          setSelectedImage(null);
                          setImagePreview(null);
                        }}
                        className="text-[10px] bg-white text-blue-700 font-bold px-3 py-1.5 rounded-xl shadow hover:bg-blue-50 transition-colors flex items-center gap-1 shrink-0"
                      >
                        Cek Berita Bergambar
                      </button>
                    </div>
                    <p className="text-xs text-blue-100 mb-4 max-w-xl">
                      Masukkan berita, rilis info, atau pesan WhatsApp berantai yang Anda terima. Model AI kami akan mendeteksi apakah pesan tersebut Hoaks atau Fakta.
                    </p>
                    <div className="flex gap-2 bg-white/10 p-1.5 rounded-2xl border border-white/20">
                      <textarea
                        rows={2}
                        value={hoaxText}
                        onChange={(e) => setHoaxText(e.target.value)}
                        placeholder="Contoh: Info BMKG gempa susulan 9 SR malam ini menghancurkan Jawa..."
                        className="flex-1 bg-transparent text-white placeholder-blue-200/70 border-0 focus:ring-0 text-xs px-3 py-1.5 outline-none resize-none font-medium"
                      />
                      <button
                        onClick={() => handleVerifyHoax()}
                        disabled={hoaxLoading || !hoaxText.trim()}
                        className="bg-white text-blue-700 hover:bg-blue-50 transition-all font-bold text-xs px-4 rounded-xl flex items-center justify-center shrink-0 disabled:opacity-50"
                      >
                        {hoaxLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : "Verifikasi"}
                      </button>
                    </div>

                    {/* Hoax Result Display */}
                    <AnimatePresence>
                      {hoaxResult && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="mt-4 pt-4 border-t border-white/20 flex flex-col sm:flex-row gap-4"
                        >
                          <div className={`px-4 py-3 rounded-2xl flex items-center gap-3 shrink-0 self-start ${
                            hoaxResult.is_hoax ? 'bg-red-500/20 text-red-200 border border-red-500/30' : 'bg-emerald-500/20 text-emerald-200 border border-emerald-500/30'
                          }`}>
                            {hoaxResult.is_hoax ? <AlertTriangle className="w-6 h-6 shrink-0" /> : <CheckCircle2 className="w-6 h-6 shrink-0" />}
                            <div>
                              <p className="text-[9px] uppercase font-bold tracking-widest opacity-80 leading-none mb-1">Hasil Deteksi</p>
                              <p className="text-base font-extrabold tracking-tight leading-none">{hoaxResult.label.toUpperCase()}</p>
                              <p className="text-[9px] font-semibold mt-1">Kepercayaan: {(hoaxResult.confidence * 100).toFixed(0)}%</p>
                            </div>
                          </div>
                          <div className="flex-1">
                            <h4 className="text-xs font-bold mb-1">Analisis AI:</h4>
                            <p className="text-[11px] text-blue-100 leading-relaxed font-medium mb-2">{hoaxResult.details}</p>
                            <h4 className="text-xs font-bold mb-1">Rekomendasi Tindakan:</h4>
                            <p className="text-[11px] text-emerald-200 leading-relaxed font-bold">{hoaxResult.action}</p>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>

                {/* News Feed */}
                <div className="flex-1 bg-white border border-slate-200 rounded-3xl p-6 shadow-sm overflow-hidden flex flex-col">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Newspaper className="w-5 h-5 text-blue-600" />
                      <h3 className="font-bold text-slate-800">Berita Kebencanaan Terkini</h3>
                    </div>
                    
                    {/* News Search bar */}
                    <div className="relative max-w-xs w-full">
                      <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        value={newsSearch}
                        onChange={(e) => setNewsSearch(e.target.value)}
                        placeholder="Cari berita..."
                        className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-4 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 font-semibold"
                      />
                    </div>
                  </div>

                  <div className="flex-1 overflow-y-auto pr-1">
                    <BmkgNews 
                      searchQuery={newsSearch}
                      onTriggerVerify={(title) => {
                        handleVerifyHoax(title);
                        // Smooth scroll back to top of the tab content if needed
                      }}
                    />
                  </div>
                </div>
              </motion.div>
            )}

            {/* TAB 3: STATS & ANALYTICS */}
            {activeTab === 'analytics' && (
              <motion.div 
                key="analytics-tab"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.2 }}
                className="flex-1 flex flex-col gap-4 overflow-y-auto max-h-[85vh] pr-1"
              >
                {/* First Row of Charts */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  
                  {/* Bar Chart: Types */}
                  <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex flex-col h-[320px]">
                    <h4 className="font-bold text-slate-800 text-xs mb-4 flex items-center gap-1.5">
                      <Activity className="w-4 h-4 text-blue-600" /> Sebaran Jumlah Bencana per Kategori
                    </h4>
                    <div className="flex-1 min-h-0">
                      {mounted && barChartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={barChartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                            <XAxis dataKey="name" tick={{ fontSize: 9, fontWeight: 600 }} tickLine={false} />
                            <YAxis tick={{ fontSize: 9, fontWeight: 600 }} width={20} tickLine={false} />
                            <Tooltip contentStyle={{ fontSize: 10, borderRadius: 12 }} />
                            <Bar dataKey="Jumlah" fill="#2563eb" radius={[4, 4, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-xs text-slate-400 font-bold">Data Tidak Tersedia</div>
                      )}
                    </div>
                  </div>

                  {/* Pie Chart: Risks */}
                  <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex flex-col h-[320px]">
                    <h4 className="font-bold text-slate-800 text-xs mb-4 flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-blue-600" /> Proporsi Tingkat Risiko Kebencanaan
                    </h4>
                    <div className="flex-1 flex items-center justify-center min-h-0">
                      {mounted && pieChartData.length > 0 ? (
                        <div className="w-full h-full flex flex-col sm:flex-row items-center justify-around">
                          <div className="w-[180px] h-[180px]">
                            <ResponsiveContainer width="100%" height="100%">
                              <PieChart>
                                <Pie
                                  data={pieChartData}
                                  innerRadius={50}
                                  outerRadius={70}
                                  paddingAngle={4}
                                  dataKey="value"
                                >
                                  {pieChartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                  ))}
                                </Pie>
                                <Tooltip formatter={(value) => [`${value} Lokasi`, 'Jumlah']} />
                              </PieChart>
                            </ResponsiveContainer>
                          </div>
                          
                          <div className="flex flex-col gap-2 shrink-0">
                            {pieChartData.map((item, idx) => (
                              <div key={idx} className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                                <span className="text-xs font-bold text-slate-600">{item.name}:</span>
                                <span className="text-xs font-black text-slate-800">{item.value} Lokasi</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-xs text-slate-400 font-bold">Data Tidak Tersedia</div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Second Row: Magnitude Line Chart & Table */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  
                  {/* Line Chart: Earthquake Magnitudes */}
                  <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex flex-col h-[280px] md:col-span-2">
                    <h4 className="font-bold text-slate-800 text-xs mb-4 flex items-center gap-1.5">
                      <Activity className="w-4 h-4 text-blue-600" /> Tren Magnitudo Gempa Terakhir (Skala Richter)
                    </h4>
                    <div className="flex-1 min-h-0">
                      {mounted && earthquakeTrends.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={earthquakeTrends}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                            <XAxis dataKey="lokasi" tick={{ fontSize: 8, fontWeight: 600 }} />
                            <YAxis domain={[0, 9]} tick={{ fontSize: 9, fontWeight: 600 }} tickLine={false} />
                            <Tooltip contentStyle={{ fontSize: 10, borderRadius: 12 }} />
                            <Line type="monotone" dataKey="Magnitudo" stroke="#ea580c" strokeWidth={2.5} activeDot={{ r: 6 }} />
                          </LineChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-xs text-slate-400 font-bold">Data Tidak Tersedia / Bukan Gempa</div>
                      )}
                    </div>
                  </div>

                  {/* High Risk Regions Table */}
                  <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex flex-col h-[280px]">
                    <h4 className="font-bold text-slate-800 text-xs mb-3 flex items-center gap-1.5">
                      <AlertCircle className="w-4 h-4 text-red-600" /> Zona Siaga Tinggi (Tinggi)
                    </h4>
                    <div className="flex-1 overflow-y-auto pr-1">
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="border-b border-slate-100 text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                            <th className="py-2">Tipe</th>
                            <th className="py-2">Lokasi</th>
                          </tr>
                        </thead>
                        <tbody>
                          {disasters.filter(d => d.risk_level === 'Tinggi').length > 0 ? (
                            disasters.filter(d => d.risk_level === 'Tinggi').map((d, index) => (
                              <tr key={index} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                                <td className="py-2.5 text-[10px] font-extrabold text-red-600 shrink-0">{d.type}</td>
                                <td className="py-2.5 text-[10px] font-semibold text-slate-700 truncate max-w-[120px]" title={d.location}>
                                  {d.location.replace("Pusat gempa berada di darat ", "").replace("Pusat gempa berada di laut ", "")}
                                </td>
                              </tr>
                            ))
                          ) : (
                            <tr>
                              <td colSpan={2} className="py-8 text-center text-xs text-slate-400 font-bold">Aman dari Zona Tinggi</td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

          </AnimatePresence>

          {/* Disaster Detail Modal */}
          <DisasterDetailModal 
            disaster={selectedDisaster} 
            onClose={() => setSelectedDisaster(null)} 
          />
        </section>

        {/* Right Column: AI Assistant Panel */}
        {activeTab !== 'analytics' && (
          <aside className="lg:col-span-4 flex flex-col overflow-hidden h-full">
             <AiAssistant selectedDisaster={selectedDisaster} />
          </aside>
        )}
      </div>

      {/* Cek Berita Bergambar Modal */}
      <AnimatePresence>
        {isImageModalOpen && (
          <div className="fixed inset-0 z-[3000] flex items-center justify-center p-4">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsImageModalOpen(false)}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
            />

            {/* Modal Box */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-xl bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-200 z-10 flex flex-col"
            >
              {/* Header */}
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-5 text-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-white" />
                  <h3 className="font-bold text-sm">Cek Berita Bergambar AI</h3>
                </div>
                <button 
                  onClick={() => setIsImageModalOpen(false)}
                  className="text-white/80 hover:text-white font-bold text-xs bg-white/10 hover:bg-white/20 w-6 h-6 rounded-full flex items-center justify-center transition-colors"
                >
                  ✕
                </button>
              </div>

              {/* Body */}
              <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
                <div>
                  <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">Judul / Tema Berita</label>
                  <input
                    type="text"
                    value={imageModalTitle}
                    onChange={(e) => setImageModalTitle(e.target.value)}
                    placeholder="Contoh: Air laut surut mendadak di pantai Ancol"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 font-semibold"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">Unggah Gambar Berita</label>
                  <div className="border-2 border-dashed border-slate-200 rounded-2xl p-4 text-center hover:bg-slate-50 transition-colors relative cursor-pointer">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageChange}
                      className="absolute inset-0 opacity-0 cursor-pointer"
                    />
                    {imagePreview ? (
                      <div className="flex flex-col items-center gap-2">
                        <img src={imagePreview} alt="Preview" className="max-h-32 object-contain rounded-lg shadow border border-slate-200" />
                        <span className="text-[10px] font-bold text-blue-600 underline">Ganti Gambar</span>
                      </div>
                    ) : (
                      <div className="py-4 text-slate-400">
                        <p className="text-xs font-bold">Klik atau seret file gambar ke sini</p>
                        <p className="text-[9px] mt-1">Format: JPG, PNG, WEBP (Maks 5MB)</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Results display */}
                {imageHoaxLoading && (
                  <div className="py-6 flex flex-col items-center justify-center gap-2 text-slate-500">
                    <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                    <span className="text-[10px] font-bold">Menganalisis metadata gambar & teks...</span>
                  </div>
                )}

                {imageHoaxResult && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 rounded-2xl border flex flex-col sm:flex-row gap-4 bg-slate-50 border-slate-200"
                  >
                    <div className={`px-4 py-3 rounded-2xl flex items-center gap-3 shrink-0 self-start text-white shadow-sm ${
                      imageHoaxResult.is_hoax ? 'bg-red-500' : 'bg-emerald-500'
                    }`}>
                      {imageHoaxResult.is_hoax ? <AlertTriangle className="w-5 h-5 shrink-0" /> : <CheckCircle className="w-5 h-5 shrink-0" />}
                      <div>
                        <p className="text-[8px] uppercase font-bold tracking-widest opacity-85 leading-none mb-1">Hasil</p>
                        <p className="text-xs font-extrabold tracking-tight leading-none">{imageHoaxResult.label}</p>
                        <p className="text-[8px] font-semibold mt-1">Akurasi: {(imageHoaxResult.confidence * 100).toFixed(0)}%</p>
                      </div>
                    </div>
                    <div className="flex-1 text-left text-slate-700">
                      <h4 className="text-[10px] font-bold text-slate-500 uppercase mb-1">Detail Analisis Gabungan:</h4>
                      <p className="text-[11px] leading-relaxed font-semibold mb-3 whitespace-pre-line">{imageHoaxResult.details}</p>
                      <h4 className="text-[10px] font-bold text-slate-500 uppercase mb-1">Rekomendasi AI:</h4>
                      <p className="text-[11px] leading-relaxed font-bold text-blue-700">{imageHoaxResult.action}</p>
                    </div>
                  </motion.div>
                )}
              </div>

              {/* Footer */}
              <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex justify-end gap-2">
                <button
                  onClick={() => setIsImageModalOpen(false)}
                  className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 transition-colors"
                >
                  Batal
                </button>
                <button
                  onClick={handleVerifyImageHoax}
                  disabled={imageHoaxLoading || !imageModalTitle.trim() || !selectedImage}
                  className="px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-bold hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  Verifikasi Berita
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Bottom Status Bar */}
      <footer className="h-10 bg-slate-900 text-white/50 px-6 flex items-center justify-between text-[9px] tracking-wider font-semibold z-20">
        <div className="flex gap-4 overflow-x-auto scrollbar-none">
          <span className="whitespace-nowrap">API LINK: {API_URL}</span>
          <span className="whitespace-nowrap">MODEL DATA: LOCAL SCKIT-LEARN PIELINE</span>
          <span className="whitespace-nowrap">BMKG TEWS SYSTEM: ONLINE</span>
        </div>
        <div className="hidden md:flex items-center gap-2 shrink-0">
          <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></span>
          <span className="text-white/80 font-bold uppercase tracking-wider">Sistem Siaga Normal</span>
        </div>
      </footer>
    </main>
  );
}
