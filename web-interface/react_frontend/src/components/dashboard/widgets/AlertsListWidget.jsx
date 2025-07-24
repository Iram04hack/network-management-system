// AlertsListWidget.jsx - Widget liste des alertes
import React from 'react';
import { AlertCircle, AlertTriangle, Activity, Clock } from 'lucide-react';
import { useTheme } from '../../../contexts/ThemeContext';

const AlertsListWidget = ({ data = [], alerts = [], isLoading = false, isCompact = false }) => {
  const { getThemeClasses } = useTheme();

  // Pas d'alertes par défaut - utilise les données de l'API
  const defaultAlerts = [];

  // Utiliser data en priorité, puis alerts, puis aucune alerte
  const alertsData = (data && data.length > 0) ? data : (alerts.length > 0 ? alerts : []);
  const criticalCount = alertsData.filter(a => 
    a.niveau === 'critique' || 
    a.niveau === 'critical' || 
    a.severity === 'critical' || 
    a.level === 'critical'
  ).length;

  const niveauColors = {
    critique: 'text-red-400 bg-red-900/20 border-l-red-500',
    critical: 'text-red-400 bg-red-900/20 border-l-red-500',
    warning: 'text-yellow-400 bg-yellow-900/20 border-l-yellow-500',
    info: 'text-blue-400 bg-blue-900/20 border-l-blue-500'
  };

  const AlertItem = ({ alert }) => {
    // Déterminer l'icône basée sur le type ou niveau
    let IconComponent = AlertTriangle;
    if (alert.icon) {
      IconComponent = alert.icon;
    } else if (alert.niveau === 'critique' || alert.niveau === 'critical') {
      IconComponent = AlertCircle;
    }
    
    // Déterminer le niveau pour la couleur
    const niveau = alert.niveau || alert.level || alert.severity || 'warning';
    
    return (
      <div className={`flex items-center space-x-2 p-2 rounded border-l-2 ${niveauColors[niveau] || niveauColors['warning']} hover:bg-opacity-50 transition-colors cursor-pointer`}>
        <IconComponent className="w-3 h-3 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className={`${getThemeClasses('text', 'dashboard')} text-xs font-medium truncate`}>
            {alert.type || alert.message || 'Alerte inconnue'}
          </div>
          <div className="flex items-center justify-between mt-1">
            <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              {alert.heure || alert.time || new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
            </span>
            {(alert.source || alert.module) && (
              <span className="text-xs bg-gray-700 px-1 rounded">
                {alert.source || alert.module}
              </span>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-sm font-semibold`}>
          Alertes Récentes
        </h3>
        <div className="flex items-center space-x-1">
          {criticalCount > 0 && (
            <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse"></div>
          )}
          <span className="text-xs bg-red-600 text-white px-1.5 py-0.5 rounded">
            {criticalCount}
          </span>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto space-y-1">
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="animate-pulse">
                <div className="flex items-center space-x-2 p-2">
                  <div className="w-3 h-3 bg-gray-600 rounded"></div>
                  <div className="flex-1 space-y-1">
                    <div className="h-3 bg-gray-600 rounded w-3/4"></div>
                    <div className="h-2 bg-gray-600 rounded w-1/2"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : alertsData.length > 0 ? (
          alertsData.slice(0, 6).map((alert) => (
            <AlertItem key={alert.id} alert={alert} />
          ))
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Activity className="w-6 h-6 text-gray-400 mx-auto mb-2" />
              <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                Aucune alerte
              </div>
            </div>
          </div>
        )}
      </div>
      
      {alertsData.length > 6 && (
        <div className="mt-2 pt-2 border-t border-gray-700">
          <button className="w-full text-xs text-blue-400 hover:text-blue-300 transition-colors">
            Voir tout ({alertsData.length - 6} autres)
          </button>
        </div>
      )}
    </div>
  );
};

export default AlertsListWidget;