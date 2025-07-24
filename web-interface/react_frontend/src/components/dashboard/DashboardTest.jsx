// DashboardTest.jsx - Composant de test pour vérifier le système de widgets
import React from 'react';
import DashboardGrid from './DashboardGrid';
import { NetworkStatusWidget, TrafficChartWidget, AlertsListWidget, SystemHealthWidget } from './widgets';

const DashboardTest = () => {
  const testWidgets = [
    {
      id: 'test-network-1',
      type: 'network-status',
      title: 'Test Statut Réseau',
      children: <NetworkStatusWidget 
        data={{
          status: 'En ligne',
          color: 'green',
          activeDevices: 8,
          totalDevices: 10,
          trend: 'up'
        }}
        isLoading={false}
      />
    },
    {
      id: 'test-traffic-1',
      type: 'traffic-chart',
      title: 'Test Trafic',
      children: <TrafficChartWidget 
        data={[
          { time: '14:00', value: 45, in: 23, out: 22 },
          { time: '14:05', value: 52, in: 28, out: 24 },
          { time: '14:10', value: 38, in: 19, out: 19 }
        ]}
        isLoading={false}
        isRealTime={true}
      />
    },
    {
      id: 'test-alerts-1',
      type: 'alerts-list',
      title: 'Test Alertes',
      children: <AlertsListWidget 
        alerts={[
          { 
            id: 1,
            type: 'Test alerte critique', 
            niveau: 'critique', 
            heure: '14:32',
            source: 'Test'
          }
        ]}
        isLoading={false}
      />
    },
    {
      id: 'test-health-1',
      type: 'system-health',
      title: 'Test Santé',
      children: <SystemHealthWidget 
        data={{
          cpu: 25,
          memory: 45,
          disk: 60,
          uptime: '99.9%'
        }}
        isLoading={false}
      />
    }
  ];

  const handleLayoutChange = (layouts) => {
    console.log('Layout changed:', layouts);
  };

  const handleWidgetAdd = (widget) => {
    console.log('Widget added:', widget);
  };

  const handleWidgetRemove = (widgetId) => {
    console.log('Widget removed:', widgetId);
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4 text-white">Test du Système de Widgets Dashboard</h1>
      <p className="text-gray-300 mb-6">
        Ce composant teste les fonctionnalités drag & drop des widgets du dashboard.
        Cliquez sur "Personnaliser" pour activer le mode édition.
      </p>
      
      <DashboardGrid
        widgets={testWidgets}
        onLayoutChange={handleLayoutChange}
        onWidgetAdd={handleWidgetAdd}
        onWidgetRemove={handleWidgetRemove}
        isEditable={true}
      />
    </div>
  );
};

export default DashboardTest;