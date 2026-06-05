'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Sparkles, Send, Loader2, Lightbulb, Mic, MicOff, Volume2, VolumeX } from 'lucide-react';

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

interface AiAssistantProps {
  selectedDisaster: Disaster | null;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function AiAssistant({ selectedDisaster }: AiAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Halo! 👋 Saya asisten **SiagaMap AI**. Klik salah satu bencana di peta atau tanya saya apa saja tentang mitigasi bencana.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([
    'Apa yang harus dilakukan saat gempa?',
    'Kontak darurat bencana',
    'Apa itu mitigasi bencana?',
  ]);
  const [isListening, setIsListening] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Voice recognition setup (STT)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechLib = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechLib) {
        const rec = new SpeechLib();
        rec.continuous = false;
        rec.interimResults = false;
        rec.lang = 'id-ID';

        rec.onstart = () => {
          setIsListening(true);
        };

        rec.onend = () => {
          setIsListening(false);
        };

        rec.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          setInput(transcript);
          handleSend(transcript);
        };

        rec.onerror = (err: any) => {
          console.error("Speech recognition error:", err);
          setIsListening(false);
        };

        setRecognition(rec);
      }
    }
  }, []);

  const toggleListening = () => {
    if (!recognition) {
      alert("Browser Anda tidak mendukung Web Speech API.");
      return;
    }
    
    if (isListening) {
      recognition.stop();
    } else {
      if (typeof window !== 'undefined') {
        window.speechSynthesis.cancel(); // Stop talking when listening
      }
      recognition.start();
    }
  };

  // Voice synthesis handler (TTS)
  const speakText = (text: string) => {
    if (isMuted || typeof window === 'undefined' || !window.speechSynthesis) return;

    window.speechSynthesis.cancel(); // Cancel any active speech

    // Clean markdown bold tokens and lists for speech clarity
    const cleanText = text
      .replace(/\*\*/g, '')
      .replace(/•/g, ', ')
      .replace(/🔴|⚠️|🌊|🌋|💧|🔥|🪨|⛈️|🔊|📢/g, '')
      .replace(/#/g, '')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'id-ID';

    // Try to get Indonesian voice
    const voices = window.speechSynthesis.getVoices();
    const idVoice = voices.find(v => v.lang.includes('id') || v.lang.includes('ID'));
    if (idVoice) {
      utterance.voice = idVoice;
    }

    window.speechSynthesis.speak(utterance);
  };

  const handleSend = async (messageText?: string) => {
    const text = messageText || input.trim();
    if (!text || isLoading) return;
    
    const userMsg = text;
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    setIsLoading(true);
    setSuggestions([]);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          disaster_context: selectedDisaster || null,
          history: messages.slice(-6),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.reply 
      }]);

      // Speak assistant response
      speakText(data.reply);

      if (data.suggestions && data.suggestions.length > 0) {
        setSuggestions(data.suggestions);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorReply = '⚠️ Maaf, terjadi kesalahan koneksi ke server AI. Pastikan backend Python berjalan di port 8000.';
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: errorReply 
      }]);
      speakText(errorReply);
    } finally {
      setIsLoading(false);
    }
  };

  // Simple markdown-like formatting (bold only for chat bubbles)
  const formatMessage = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return part.split('\n').map((line, j) => (
        <span key={`${i}-${j}`}>
          {j > 0 && <br />}
          {line}
        </span>
      ));
    });
  };

  return (
    <div className="flex flex-col h-full min-h-[500px] max-h-[700px] bg-white border border-slate-200 rounded-3xl shadow-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-100 bg-gradient-to-r from-blue-500/5 to-cyan-500/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-600 animate-pulse" />
          <h2 className="font-bold text-slate-800 text-sm">Asisten SiagaMap AI</h2>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-[9px] font-bold px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full uppercase">
            Chatbot
          </span>
          <button
            onClick={() => {
              const newMuted = !isMuted;
              setIsMuted(newMuted);
              if (newMuted && typeof window !== 'undefined') {
                window.speechSynthesis.cancel();
              }
            }}
            className={`p-1.5 rounded-lg border transition-all ${
              isMuted 
                ? 'bg-red-50 text-red-500 border-red-100 hover:bg-red-100' 
                : 'bg-blue-50 text-blue-600 border-blue-100 hover:bg-blue-100'
            }`}
            title={isMuted ? "Aktifkan suara" : "Bisukan suara"}
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
        {messages.map((msg, i) => (
          <motion.div 
            key={i} 
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.15 }}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`relative max-w-[85%] p-3.5 rounded-2xl text-xs leading-relaxed whitespace-pre-wrap flex flex-col ${
              msg.role === 'user' 
                ? 'bg-blue-600 text-white rounded-tr-none shadow-sm' 
                : 'bg-slate-50 text-slate-700 border border-slate-200/80 rounded-tl-none'
            }`}>
              <div>
                {msg.role === 'assistant' ? formatMessage(msg.content) : msg.content}
              </div>
              
              {/* Speaker icon inside bubble for replay */}
              {msg.role === 'assistant' && (
                <button
                  onClick={() => speakText(msg.content)}
                  className="mt-2 self-end text-[9px] font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1 bg-white hover:bg-blue-50 px-2 py-0.5 rounded border border-slate-200 shadow-sm transition-colors"
                >
                  <Volume2 className="w-3 h-3" /> Dengar Audio
                </button>
              )}
            </div>
          </motion.div>
        ))}

        {/* Loading indicator */}
        <AnimatePresence>
          {isLoading && (
            <motion.div 
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex justify-start"
            >
              <div className="bg-slate-50 text-slate-500 border border-slate-200 rounded-2xl rounded-tl-none p-3.5 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                <span className="text-[10px] font-bold">Asisten sedang mengetik & berpikir...</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Disaster context indicator */}
        {selectedDisaster && (
          <div className="mt-2 p-3 bg-blue-50/50 border border-blue-100 rounded-2xl">
            <p className="text-[9px] font-bold text-blue-600 uppercase mb-1">Fokus Terkait</p>
            <p className="text-[10px] font-bold text-slate-700">{selectedDisaster.type} di {selectedDisaster.location}</p>
          </div>
        )}

        {/* Suggestion chips */}
        {suggestions.length > 0 && !isLoading && (
          <div className="mt-2 flex flex-col gap-1.5">
            <div className="flex items-center gap-1.5 text-slate-400">
              <Lightbulb className="w-3 h-3 text-amber-500 animate-pulse" />
              <span className="text-[9px] font-bold uppercase tracking-wider">Saran pertanyaan</span>
            </div>
            {suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => handleSend(s)}
                className="text-left text-[11px] px-3.5 py-2 bg-slate-50 hover:bg-blue-50/50 border border-slate-200/80 rounded-xl text-slate-600 hover:text-blue-600 transition-all font-bold"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Footer / Input block */}
      <div className="p-4 bg-slate-50 border-t border-slate-150 flex gap-2 items-center">
        {/* Mic Toggle Button */}
        <button
          onClick={toggleListening}
          className={`w-10 h-10 rounded-xl flex items-center justify-center border transition-all ${
            isListening 
              ? 'bg-red-500 text-white border-red-400 animate-pulse shadow-lg shadow-red-500/20' 
              : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-slate-900'
          }`}
          title={isListening ? "Hentikan merekam suara" : "Tanya lewat suara"}
        >
          {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
        </button>

        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder={isListening ? "Mendengarkan suara Anda..." : "Tanya mitigasi bencana..."}
          disabled={isLoading}
          className="flex-1 bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50 font-semibold text-slate-800"
        />
        
        <button 
          onClick={() => handleSend()}
          disabled={isLoading || !input.trim()}
          className="w-10 h-10 bg-blue-600 text-white rounded-xl flex items-center justify-center hover:bg-blue-700 transition-all shadow-md shadow-blue-500/10 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
        </button>
      </div>
    </div>
  );
}
