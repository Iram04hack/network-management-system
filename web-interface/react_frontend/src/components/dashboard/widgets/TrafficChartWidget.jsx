// TrafficChartWidget.jsx - Widget graphique du trafic réseau
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, RefreshCw } from 'lucide-react';
import { useTheme } from '../../../contexts/ThemeContext';

const TrafficChartWidget = ({ data = [], isLoading = false, isRealTime = false, isCompact = false }) => {
  const { getThemeClasses } = useTheme();

  // Données par défaut si pas de données
  const defaultData = [
    { time: '14:00', value: 45, in: 23, out: 22 },
    { time: '14:05', value: 52, in: 28, out: 24 },
    { time: '14:10', value: 38, in: 19, out: 19 },
    { time: '14:15', value: 65, in: 35, out: 30 },
    { time: '14:20', value: 48, in: 25, out: 23 },
    { time: '14:25', value: 58, in: 32, out: 26 },
    { time: '14:30', value: 42, in: 22, out: 20 }
  ];

  // Support des données de DashboardHome
  const trafficData = data.length > 0 ? data.map(item => ({
    time: item.time,
    value: item.upload + item.download,
    in: item.download,
    out: item.upload
  })) : defaultData;

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className={`${getThemeClasses('text', 'dashboard')} text-sm font-semibold`}>
            Trafic Réseau
          </h3>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
            {isRealTime ? 'Temps réel' : 'Données historiques'}
          </p>
        </div>
        <div className="flex items-center space-x-1">
          {isLoading && <RefreshCw className="w-3 h-3 text-blue-400 animate-spin" />}
          <Activity className="w-4 h-4 text-blue-400" />
        </div>
      </div>
      
      <div className="flex-1 min-h-0">
        {isLoading ? (
          <div className="h-full flex items-center justify-center">
            <div className="animate-pulse text-center">
              <div className="w-12 h-12 bg-gray-600 rounded mx-auto mb-2"></div>
              <div className="text-xs text-gray-400">Chargement...</div>
            </div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trafficData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="time" 
                stroke="#9CA3AF"
                fontSize={10}
                axisLine={false}
                tickLine={false}
              />
              <YAxis 
                stroke="#9CA3AF"
                fontSize={10}
                axisLine={false}
                tickLine={false}
                width={30}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '4px',
                  color: '#fff',
                  fontSize: '12px'
                }}
                formatter={(value, name) => [
                  `${value} Mb/s`, 
                  name === 'value' ? 'Total' : name === 'in' ? 'Entrant' : 'Sortant'
                ]}
              />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#3B82F6" 
                strokeWidth={2}
                dot={false}
                name="total"
              />
              {trafficData[0]?.in !== undefined && (
                <>
                  <Line 
                    type="monotone" 
                    dataKey="in" 
                    stroke="#10B981" 
                    strokeWidth={1}
                    dot={false}
                    strokeDasharray="3 3"
                    name="in"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="out" 
                    stroke="#F59E0B" 
                    strokeWidth={1}
                    dot={false}
                    strokeDasharray="2 2"
                    name="out"
                  />
                </>
              )}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

export default TrafficChartWidget;