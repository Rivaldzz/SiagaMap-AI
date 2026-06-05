'use client';

import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { ShieldCheck, Loader2, ExternalLink } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface NewsItem {
  id: string;
  title: string;
  link?: string;
  date: string;
  category: string;
  summary?: string;
}

interface BmkgNewsProps {
  searchQuery: string;
  onTriggerVerify: (title: string) => void;
}

export default function BmkgNews({ searchQuery, onTriggerVerify }: BmkgNewsProps) {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchNews() {
      try {
        const res = await fetch(`${API_URL}/api/news`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setNews(data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch BMKG news", err);
        setError("Gagal memuat berita. Pastikan server backend berjalan.");
      } finally {
        setLoading(false);
      }
    }

    fetchNews();
  }, []);

  const filteredNews = news.filter(item => {
    const query = searchQuery.toLowerCase().trim();
    if (!query) return true;
    return (
      item.title.toLowerCase().includes(query) ||
      (item.summary && item.summary.toLowerCase().includes(query)) ||
      item.category.toLowerCase().includes(query)
    );
  });

  if (loading) {
    return (
      <div className="py-12 flex flex-col items-center justify-center gap-2 text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
        <span className="text-xs font-semibold">Mengambil berita kebencanaan BMKG...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-8 text-center">
        <p className="text-xs font-bold text-red-500">{error}</p>
        <button 
          onClick={() => { setLoading(true); }}
          className="mt-2 text-[10px] font-bold text-blue-600 underline"
        >
          Coba Lagi
        </button>
      </div>
    );
  }

  if (filteredNews.length === 0) {
    return (
      <div className="py-12 text-center text-xs text-slate-400 font-bold">
        Tidak ditemukan berita yang cocok.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {filteredNews.map((item, i) => (
        <motion.div 
          key={item.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
          className="group bg-slate-50 hover:bg-blue-50/20 p-5 rounded-2xl border border-slate-200/80 shadow-sm transition-all flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between gap-4 mb-3">
              <span className="text-[9px] font-bold px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full uppercase">
                {item.category}
              </span>
              <span className="text-[9px] text-slate-400 font-semibold">{item.date}</span>
            </div>
            
            <h4 className="text-xs font-extrabold text-slate-800 group-hover:text-blue-600 transition-colors mb-2 line-clamp-2 leading-snug">
              {item.title}
            </h4>
            
            <p className="text-[10px] text-slate-500 font-medium leading-relaxed mb-4 line-clamp-3">
              {item.summary || "Klik selengkapnya untuk membaca liputan lengkap di portal resmi."}
            </p>
          </div>

          <div className="flex items-center justify-between border-t border-slate-100 pt-3 mt-1">
            <button
              onClick={() => onTriggerVerify(item.title)}
              className="text-[10px] font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 bg-indigo-50 hover:bg-indigo-100/70 px-2.5 py-1 rounded-lg transition-colors"
            >
              <ShieldCheck className="w-3.5 h-3.5" /> Cek Hoaks AI
            </button>
            
            {item.link && (
              <a 
                href={item.link} 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-[10px] font-bold text-slate-500 hover:text-slate-800 flex items-center gap-1"
              >
                Sumber Resmi <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
