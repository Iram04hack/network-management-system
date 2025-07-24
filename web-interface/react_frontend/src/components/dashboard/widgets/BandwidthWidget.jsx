// BandwidthWidget.jsx - Widget utilisation bande passante
import React from 'react';
import { Wifi, TrendingUp, TrendingDown } from 'lucide-react';
import { useTheme } from '../../../contexts/ThemeContext';

const BandwidthWidget = ({ data = {}, isLoading = false, isCompact = false }) => {
  const { getThemeClasses } = useTheme();
  
  const {
    current = 145.7,
    max = 200,
    unit = 'Mbps'
  } = data;

  const percentage = Math.round((current / max) * 100);
  const isHigh = percentage > 80;

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-sm font-semibold`}>
          Bande Passante
        </h3>
        <Wifi className={`w-4 h-4 ${isHigh ? 'text-red-400' : 'text-blue-400'}`} />
      </div>
      
      <div className="flex-1 flex flex-col justify-center space-y-3">
        {isLoading ? (
          <div className="animate-pulse space-y-3">
            <div className="h-8 bg-gray-600 rounded w-24"></div>
            <div className="h-2 bg-gray-600 rounded w-full"></div>
          </div>
        ) : (
          <>
            <div className="text-center">
              <div className={`text-2xl font-bold ${isHigh ? 'text-red-400' : 'text-blue-400'}`}>
                {current} {unit}
              </div>
              <div className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
                sur {max} {unit} max
              </div>
            </div>
            
            {/* Barre de progression circulaire simplifiée */}
            <div className="relative">
              <div className="w-full bg-gray-700 rounded-full h-3">
                <div 
                  className={`h-3 rounded-full transition-all duration-300 ${
                    isHigh ? 'bg-red-400' : percentage > 60 ? 'bg-yellow-400' : 'bg-green-400'
                  }`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
              <div className="flex justify-between text-xs mt-1">
                <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>0</span>
                <span className={`font-medium ${isHigh ? 'text-red-400' : 'text-blue-400'}`}>
                  {percentage}%
                </span>
                <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>{max}</span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default BandwidthWidget;