import { Check } from 'lucide-react';
import { ImageWithFallback } from './figma/ImageWithFallback';

interface DetectionCardProps {
  id: string;
  vehicleImage: string;
  plateImage: string;
  plateNumber: string;
  timestamp: string;
  confidence: number;
}

export function DetectionCard({
  vehicleImage,
  plateImage,
  plateNumber,
  timestamp,
  confidence,
}: DetectionCardProps) {
  return (
    <div className="bg-[#242424] rounded-lg overflow-hidden border border-[#333333] hover:border-[#00FFFF] transition-all duration-300">
      {/* Top Section - Vehicle Image */}
      <div className="w-full aspect-video bg-[#1A1A1A] relative overflow-hidden">
        <ImageWithFallback
          src={vehicleImage}
          alt="Vehicle capture"
          className="w-full h-full object-cover"
        />
      </div>

      {/* Bottom Section - Evidence & Data */}
      <div className="p-3 sm:p-4 flex gap-3 sm:gap-4">
        {/* Bottom-Left - Plate Thumbnail */}
        <div className="w-20 h-20 sm:w-24 sm:h-24 flex-shrink-0">
          <ImageWithFallback
            src={plateImage}
            alt="License plate capture"
            className="w-full h-full object-cover rounded border-2 border-[#333333]"
          />
        </div>

        {/* Bottom-Right - Processed Data */}
        <div className="flex-1 flex flex-col justify-center gap-2 min-w-0">
          {/* License Plate Display */}
          <div className="bg-white rounded px-2 sm:px-3 py-1.5 sm:py-2 border-2 border-[#222222] shadow-lg">
            <div className="license-plate-text text-black text-base sm:text-xl md:text-2xl text-center break-all">
              {plateNumber}
            </div>
          </div>

          {/* Metadata */}
          <div className="flex items-center gap-1.5 sm:gap-2 text-[10px] sm:text-xs text-[#A0A0A0] flex-wrap">
            <span className="whitespace-nowrap">{timestamp}</span>
            <span className="text-[#333333]">|</span>
            <div className="flex items-center gap-1 whitespace-nowrap">
              {confidence >= 90 && (
                <Check className="w-3 h-3 text-[#00FF41]" />
              )}
              <span className={confidence >= 90 ? 'text-[#00FF41]' : 'text-[#FFAA00]'}>
                Confidence: {confidence}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}