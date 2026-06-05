import { NextResponse } from 'next/server';

export async function GET() {
  // Simulasi data BMKG
  const mockData = [
    {
      id: "20240510001",
      type: "Gempa Bumi",
      magnitude: 5.8,
      depth: "10 km",
      location: "Barat Daya Mukomuko, Bengkulu",
      coordinates: [-2.57, 101.12],
      time: "10 Mei 2024, 12:00 WIB",
      risk_level: "Sedang"
    },
    {
      id: "20240510002",
      type: "Prakiraan Cuaca Ekstrem",
      magnitude: null,
      depth: null,
      location: "Jakarta Timur, DKI Jakarta",
      coordinates: [-6.22, 106.90],
      time: "10 Mei 2024, 14:00 WIB",
      risk_level: "Rendah"
    },
    {
      id: "20240510003",
      type: "Erupsi Gunung Api",
      magnitude: null,
      depth: null,
      location: "Gn. Merapi, Jawa Tengah",
      coordinates: [-7.54, 110.44],
      time: "10 Mei 2024, 08:00 WIB",
      risk_level: "Tinggi"
    }
  ];

  return NextResponse.json(mockData);
}
