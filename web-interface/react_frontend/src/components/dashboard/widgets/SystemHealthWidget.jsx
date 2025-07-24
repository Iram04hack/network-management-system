// SystemHealthWidget.jsx - Widget santé du système
import React from 'react';
import { Cpu, HardDrive, Zap, Clock } from 'lucide-react';
import { useTheme } from '../../../contexts/ThemeContext';

const SystemHealthWidget = ({ data = {}, isLoading = false, isCompact = false }) => {
  const { getThemeClasses } = useTheme();
  
  const {
    cpu = 0,
    memory = 0,
    disk = 0,
    uptime = 'N/A'
  } = data;
  
  // Calculer l'état global du système
  const globalHealth = {
    value: Math.round((cpu + memory + disk) / 3),
    status: cpu > 80 || memory > 80 || disk > 80 ? 'critical' : 
            cpu > 60 || memory > 60 || disk > 60 ? 'warning' : 'healthy'
  };

  const getHealthColor = (value) => {
    if (value > 80) return 'text-red-400';
    if (value > 60) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getHealthBgColor = (value) => {
    if (value > 80) return 'bg-red-400';
    if (value > 60) return 'bg-yellow-400';
    return 'bg-green-400';
  };

  const ProgressBar = ({ value, icon: Icon, label }) => (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-1">
          <Icon className="w-3 h-3 text-gray-400" />
          <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
            {label}
          </span>
        </div>
        <span className={`text-xs font-medium ${getHealthColor(value)}`}>
          {value}%
        </span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-1.5">
        <div 
          className={`h-1.5 rounded-full transition-all duration-300 ${getHealthBgColor(value)}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-sm font-semibold`}>
          Santé Système
        </h3>
        <Zap className="w-4 h-4 text-green-400" />
      </div>
      
      <div className="flex-1 space-y-3">
        {isLoading ? (
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="space-y-1">
                <div className="flex justify-between">
                  <div className="h-3 bg-gray-600 rounded w-12"></div>
                  <div className="h-3 bg-gray-600 rounded w-8"></div>
                </div>
                <div className="h-1.5 bg-gray-600 rounded w-full"></div>
              </div>
            ))}
          </div>
        ) : (
          <>
            <ProgressBar value={cpu} icon={Cpu} label="CPU" />
            <ProgressBar value={memory} icon={HardDrive} label="RAM" />
            <ProgressBar value={disk} icon={HardDrive} label="Disque" />
            
            {/* État global */}
            <div className="pt-2 border-t border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <Zap className={`w-3 h-3 ${
                    globalHealth.status === 'critical' ? 'text-red-400' :
                    globalHealth.status === 'warning' ? 'text-yellow-400' : 'text-green-400'
                  }`} />
                  <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    État global
                  </span>
                </div>
                <span className={`text-xs font-medium ${
                  globalHealth.status === 'critical' ? 'text-red-400' :
                  globalHealth.status === 'warning' ? 'text-yellow-400' : 'text-green-400'
                }`}>
                  {globalHealth.status === 'critical' ? 'Critique' :
                   globalHealth.status === 'warning' ? 'Attention' : 'Bon'}
                </span>
              </div>
            </div>
            
            {/* Uptime */}
            <div className="pt-2 border-t border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <Clock className="w-3 h-3 text-gray-400" />
                  <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    Uptime
                  </span>
                </div>
                <span className="text-xs font-medium text-green-400">
                  {uptime}
                </span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default SystemHealthWidget;