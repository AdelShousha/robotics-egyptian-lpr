import { useState, useEffect } from 'react';
import { DetectionCard } from './components/DetectionCard';

// API URL - use environment variable or default to localhost for development
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Detection {
  id: number;
  car_image: string;
  lp_image: string;
  lp_number: string;
  confidence: number;
  created_at: string;
}

interface DashboardData {
  vehicles_today: number;
  last_detection: string | null;
  detections: Detection[];
}

function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
}

function formatLastDetection(isoString: string | null): string {
  if (!isoString) return 'No detections';

  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export default function App() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch(`${API_URL}/api/dashboard`);
      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data');
      }
      const dashboardData: DashboardData = await response.json();
      setData(dashboardData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    // Refresh data every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#121212]">
      {/* Header Bar */}
      <header className="sticky top-0 z-50 bg-[#1E1E1E] border-b border-[#333333] px-4 md:px-6 py-3 md:py-4">
        <div className="max-w-[1800px] mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4">
          {/* Left Side - Branding & Status */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-6 w-full sm:w-auto">
            <h1 className="text-[#00FFFF] tracking-wide text-lg sm:text-xl md:text-2xl">Egyptian Plate Recognition</h1>

            <div className="flex items-center gap-2 px-3 py-1.5 bg-[#242424] rounded-md border border-[#333333]">
              <div className="w-2 h-2 bg-[#00FF41] rounded-full pulse-dot"></div>
              <span className="text-xs sm:text-sm text-[#00FF41]">Live Monitor - Active</span>
            </div>
          </div>

          {/* Right Side - Data Summary */}
          <div className="flex items-center gap-3 sm:gap-4 text-xs sm:text-sm w-full sm:w-auto justify-between sm:justify-end">
            <div className="flex items-center gap-2">
              <span className="text-[#A0A0A0]">Vehicles Today:</span>
              <span className="text-[#00FFFF]">{data?.vehicles_today ?? 0}</span>
            </div>

            <div className="w-px h-4 bg-[#333333]"></div>

            <div className="flex items-center gap-2">
              <span className="text-[#A0A0A0]">Last Detection:</span>
              <span className="text-[#00FFFF]">{formatLastDetection(data?.last_detection ?? null)}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - Detection Grid */}
      <main className="max-w-[1800px] mx-auto px-4 md:px-6 py-6 md:py-8">
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="text-[#A0A0A0] text-lg">Loading detections...</div>
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="text-[#FF6B6B] text-lg">Error: {error}</div>
            <button
              onClick={() => { setLoading(true); fetchDashboardData(); }}
              className="px-4 py-2 bg-[#00FFFF] text-black rounded hover:bg-[#00CCCC] transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && data && data.detections.length === 0 && (
          <div className="flex items-center justify-center py-20">
            <div className="text-[#A0A0A0] text-lg">No detections yet. Waiting for vehicles...</div>
          </div>
        )}

        {!loading && !error && data && data.detections.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
            {data.detections.map((detection) => (
              <DetectionCard
                key={detection.id}
                id={String(detection.id)}
                vehicleImage={detection.car_image}
                plateImage={detection.lp_image}
                plateNumber={detection.lp_number}
                timestamp={formatTimestamp(detection.created_at)}
                confidence={Math.round(detection.confidence * 100)}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
