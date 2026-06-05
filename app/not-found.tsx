import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 text-slate-800 p-4">
      <h2 className="text-2xl font-bold mb-2">Halaman Tidak Ditemukan</h2>
      <p className="text-sm text-slate-500 mb-6 font-medium">Maaf, halaman yang Anda cari tidak dapat ditemukan.</p>
      <Link href="/" className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-lg shadow-blue-200 transition-all text-sm">
        Kembali ke Beranda
      </Link>
    </div>
  );
}
