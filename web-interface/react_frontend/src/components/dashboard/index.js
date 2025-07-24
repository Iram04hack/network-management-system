/**
 * Dashboard Components - Export des composants modernisés
 * Permet d'utiliser facilement tous les composants du dashboard
 */

// Composants principaux
export { default as ModernDashboard } from './ModernDashboard';
export { default as DashboardDesigner } from './DashboardDesigner';
export { default as RealtimeNotifications } from './RealtimeNotifications';
export { default as QuickActions } from './QuickActions';

// Hook personnalisé
export { useDashboard } from '../../hooks/useDashboard';

// Composant par défaut
export { default } from './ModernDashboard';