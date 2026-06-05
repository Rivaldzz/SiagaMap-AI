'use client';

import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useEffect } from 'react';

// Fix for default user location marker icon in Leaflet
const userIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

// Custom Leaflet markers for various disasters
const getDisasterIcon = (type: string, riskLevel: string) => {
  let color = 'bg-blue-500';
  let ringColor = 'border-blue-300';
  let pulseHtml = '';

  if (riskLevel === 'Tinggi') {
    color = 'bg-red-600';
    ringColor = 'border-red-400';
    pulseHtml = '<span class="absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75 animate-ping"></span>';
  } else if (riskLevel === 'Sedang') {
    color = 'bg-amber-500';
    ringColor = 'border-amber-300';
    pulseHtml = '<span class="absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-50 animate-ping"></span>';
  }

  // Icon type mapping
  let emoji = '⚠️';
  const t = type.toLowerCase();
  if (t.includes('gempa bumi')) {
    emoji = '🔊';
  } else if (t.includes('gempa dirasakan')) {
    emoji = '📢';
  } else if (t.includes('tsunami')) {
    emoji = '🌊';
  } else if (t.includes('banjir')) {
    emoji = '💧';
  } else if (t.includes('kebakaran') || t.includes('api')) {
    emoji = '🔥';
  } else if (t.includes('longsor')) {
    emoji = '🪨';
  } else if (t.includes('erupsi') || t.includes('gunung')) {
    emoji = '🌋';
  } else if (t.includes('cuaca') || t.includes('hujan') || t.includes('angin')) {
    emoji = '⛈️';
  } else if (t.includes('gelombang') || t.includes('maritim')) {
    emoji = '🌊';
  }

  return L.divIcon({
    html: `
      <div class="relative flex items-center justify-center w-10 h-10">
        ${pulseHtml}
        <div class="relative z-10 flex items-center justify-center w-8 h-8 rounded-full text-white font-bold shadow-xl border-2 ${ringColor} ${color} transition-all transform hover:scale-125">
          <span class="text-base leading-none">${emoji}</span>
        </div>
      </div>
    `,
    className: 'custom-leaflet-icon',
    iconSize: [40, 40],
    iconAnchor: [20, 20],
  });
};

interface Disaster {
  id: string;
  type: string;
  location: string;
  coordinates: [number, number];
  magnitude?: number;
  risk_level: string;
  time: string;
}

interface MapDisplayProps {
  disasters: Disaster[];
  onSelectDisaster: (disaster: Disaster) => void;
  userLocation: [number, number] | null;
}

function RecenterMap({ position }: { position: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    if (position) {
      map.setView(position, 6);
    }
  }, [position, map]);
  return null;
}

export default function MapDisplay({ disasters, onSelectDisaster, userLocation }: MapDisplayProps) {
  const center: [number, number] = userLocation || [-2.5489, 118.0149]; // Center of Indonesia

  return (
    <div className="w-full h-full min-h-[500px]">
      <MapContainer center={center} zoom={5} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {userLocation && (
          <Marker position={userLocation} icon={userIcon}>
            <Popup>Lokasi Anda</Popup>
          </Marker>
        )}
        {disasters.map((disaster) => (
          <Marker 
            key={disaster.id} 
            position={disaster.coordinates} 
            icon={getDisasterIcon(disaster.type, disaster.risk_level)}
            eventHandlers={{
              click: () => onSelectDisaster(disaster),
            }}
          >
            <Popup>
              <div className="p-1">
                <p className="font-bold">{disaster.type}</p>
                <p className="text-xs">{disaster.location}</p>
                {disaster.magnitude && disaster.magnitude > 0 && <p className="text-xs">Mag: {disaster.magnitude}</p>}
                <p className={`text-xs font-bold ${disaster.risk_level === 'Tinggi' ? 'text-red-600' : 'text-blue-600'}`}>
                  Risiko: {disaster.risk_level}
                </p>
              </div>
            </Popup>
          </Marker>
        ))}
        {userLocation && <RecenterMap position={userLocation} />}
      </MapContainer>
    </div>
  );
}

