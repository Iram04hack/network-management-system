// index.js - Export de tous les widgets du dashboard
export { default as NetworkStatusWidget } from './NetworkStatusWidget';
export { default as TrafficChartWidget } from './TrafficChartWidget';
export { default as AlertsListWidget } from './AlertsListWidget';
export { default as SystemHealthWidget } from './SystemHealthWidget';
export { default as BandwidthWidget } from './BandwidthWidget';
export { default as DeviceCountWidget } from './DeviceCountWidget';

// Imports des nouveaux widgets
import BandwidthWidget from './BandwidthWidget';
import DeviceCountWidget from './DeviceCountWidget';

// Widget factory pour créer dynamiquement les widgets
export const createWidget = (type, props = {}) => {
  const widgets = {
    'network-status': NetworkStatusWidget,
    'traffic-chart': TrafficChartWidget,
    'alerts-list': AlertsListWidget,
    'system-health': SystemHealthWidget,
    'BandwidthWidget': BandwidthWidget,
    'DeviceCountWidget': DeviceCountWidget
  };
  
  const Widget = widgets[type];
  return Widget ? Widget : null;
};

// Configuration des widgets disponibles
export const widgetConfigs = {
  'network-status': {
    name: 'Statut Réseau',
    defaultSize: { w: 4, h: 4 },
    minSize: { w: 3, h: 3 },
    component: 'NetworkStatusWidget'
  },
  'traffic-chart': {
    name: 'Graphique Trafic',
    defaultSize: { w: 6, h: 4 },
    minSize: { w: 4, h: 3 },
    component: 'TrafficChartWidget'
  },
  'alerts-list': {
    name: 'Liste Alertes',
    defaultSize: { w: 4, h: 5 },
    minSize: { w: 3, h: 4 },
    component: 'AlertsListWidget'
  },
  'system-health': {
    name: 'Santé Système',
    defaultSize: { w: 4, h: 4 },
    minSize: { w: 3, h: 3 },
    component: 'SystemHealthWidget'
  },
  'bandwidth-usage': {
    name: 'Bande Passante',
    defaultSize: { w: 4, h: 3 },
    minSize: { w: 3, h: 3 },
    component: 'BandwidthWidget'
  },
  'device-count': {
    name: 'Appareils Connectés',
    defaultSize: { w: 3, h: 3 },
    minSize: { w: 3, h: 3 },
    component: 'DeviceCountWidget'
  }
};