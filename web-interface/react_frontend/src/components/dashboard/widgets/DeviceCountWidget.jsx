// DeviceCountWidget.jsx - Widget comptage d'appareils
import React from 'react';
import { Router, Smartphone, Plus, AlertCircle } from 'lucide-react';
import { useTheme } from '../../../contexts/ThemeContext';

const DeviceCountWidget = ({ data = {}, isLoading = false, isCompact = false }) => {
  const { getThemeClasses } = useTheme();
  
  const {
    total = 42,
    online = 38,
    offline = 4,
    new: newDevices = 2
  } = data;

  const onlinePercentage = Math.round((online / total) * 100);

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-sm font-semibold`}>
          Appareils
        </h3>
        <Router className="w-4 h-4 text-blue-400" />
      </div>
      
      <div className="flex-1 space-y-3">
        {isLoading ? (
          <div className="animate-pulse space-y-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="flex justify-between">
                <div className="h-4 bg-gray-600 rounded w-16"></div>
                <div className="h-4 bg-gray-600 rounded w-8"></div>
              </div>
            ))}
          </div>
        ) : (
          <>
            {/* Total et pourcentage en ligne */}
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">{total}</div>
              <div className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
                Total appareils
              </div>
            </div>
            
            {/* Détails */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
                    En ligne
                  </span>
                </div>
                <span className="text-xs font-medium text-green-400">{online}</span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                  <span className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
                    Hors ligne
                  </span>
                </div>
                <span className="text-xs font-medium text-red-400">{offline}</span>
              </div>
              
              {newDevices > 0 && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Plus className="w-2 h-2 text-yellow-400" />
                    <span className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
                      Nouveaux
                    </span>
                  </div>
                  <span className="text-xs font-medium text-yellow-400">{newDevices}</span>
                </div>
              )}
            </div>
            
            {/* Barre de progression */}
            <div className="pt-2 border-t border-gray-700">
              <div className="flex justify-between text-xs mb-1">
                <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>
                  Disponibilité
                </span>
                <span className="text-green-400 font-medium">{onlinePercentage}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-1.5">
                <div 
                  className="bg-green-400 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${onlinePercentage}%` }}
                />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default DeviceCountWidget;