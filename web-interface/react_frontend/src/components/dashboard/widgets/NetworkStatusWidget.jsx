// NetworkStatusWidget.jsx - Widget pour l'état du réseau
import React from 'react';
import { Globe, TrendingUp, TrendingDown } from 'lucide-react';
import { useTheme } from '../../../contexts/ThemeContext';

const NetworkStatusWidget = ({ data = {}, isLoading = false, isCompact = false }) => {
  const { getThemeClasses } = useTheme();
  
  const {
    status = 'Chargement...',
    color = 'gray',
    activeDevices = 0,
    totalDevices = 0,
    trend = 'stable'
  } = data;
  
  // Calculer le pourcentage de disponibilité
  const availabilityPercent = totalDevices > 0 ? Math.round((activeDevices / totalDevices) * 100) : 0;

  const colorClasses = {
    green: 'text-green-400',
    yellow: 'text-yellow-400',
    red: 'text-red-400'
  };

  const TrendIcon = trend === 'up' ? TrendingUp : TrendingDown;

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <h3 className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
          Statut Réseau
        </h3>
        <div className="flex items-center space-x-1">
          <TrendIcon className={`w-3 h-3 ${trend === 'up' ? 'text-green-400' : 'text-red-400'}`} />
          <Globe className={`w-4 h-4 ${colorClasses[color]}`} />
        </div>
      </div>
      
      <div className="flex-1 flex flex-col justify-center space-y-3">
        {isLoading ? (
          <div className="animate-pulse space-y-2">
            <div className="h-6 bg-gray-600 rounded w-20"></div>
            <div className="h-4 bg-gray-600 rounded w-16"></div>
          </div>
        ) : (
          <>
            <div>
              <div className={`text-2xl font-bold ${colorClasses[color]}`}>
                {status}
              </div>
              <div className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
                {activeDevices}/{totalDevices} équipements actifs
              </div>
            </div>
            
            {/* Barre de progression */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Disponibilité</span>
                <span className={`${getThemeClasses('text', 'dashboard')}`}>
                  {availabilityPercent}%
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-1.5">
                <div 
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    color === 'green' ? 'bg-green-400' : 
                    color === 'yellow' ? 'bg-yellow-400' : 'bg-red-400'
                  }`}
                  style={{ width: `${availabilityPercent}%` }}
                />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default NetworkStatusWidget;