// useDashboardWidgets.js - Hook pour la gestion des widgets du dashboard
import { useState, useCallback } from 'react';

export const useDashboardWidgets = () => {
  const [widgets, setWidgets] = useState([]);
  const [layouts, setLayouts] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // API calls pour les widgets (à connecter avec le backend)
  const fetchWidgets = useCallback(async () => {
    setLoading(true);
    try {
      // TODO: Remplacer par l'API réelle /dashboard/widgets/
      // const response = await fetch('/api/dashboard/widgets/');
      // const data = await response.json();
      
      // Pour l'instant, utiliser localStorage
      const savedWidgets = localStorage.getItem('dashboard-widgets');
      const savedLayouts = localStorage.getItem('dashboard-layouts');
      
      if (savedWidgets) {
        setWidgets(JSON.parse(savedWidgets));
      }
      if (savedLayouts) {
        setLayouts(JSON.parse(savedLayouts));
      }
      
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Erreur lors du chargement des widgets:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const saveWidget = useCallback(async (widget) => {
    try {
      // TODO: Remplacer par l'API réelle
      // const response = await fetch('/api/dashboard/widgets/', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(widget)
      // });
      
      // Pour l'instant, utiliser localStorage
      const currentWidgets = [...widgets, widget];
      setWidgets(currentWidgets);
      localStorage.setItem('dashboard-widgets', JSON.stringify(currentWidgets));
      
      return widget;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [widgets]);

  const updateWidget = useCallback(async (widgetId, updates) => {
    try {
      // TODO: Remplacer par l'API réelle
      // const response = await fetch(`/api/dashboard/widgets/${widgetId}/`, {
      //   method: 'PATCH',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(updates)
      // });
      
      const updatedWidgets = widgets.map(w => 
        w.id === widgetId ? { ...w, ...updates } : w
      );
      setWidgets(updatedWidgets);
      localStorage.setItem('dashboard-widgets', JSON.stringify(updatedWidgets));
      
      return updatedWidgets.find(w => w.id === widgetId);
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [widgets]);

  const deleteWidget = useCallback(async (widgetId) => {
    try {
      // TODO: Remplacer par l'API réelle
      // await fetch(`/api/dashboard/widgets/${widgetId}/`, {
      //   method: 'DELETE'
      // });
      
      const filteredWidgets = widgets.filter(w => w.id !== widgetId);
      setWidgets(filteredWidgets);
      localStorage.setItem('dashboard-widgets', JSON.stringify(filteredWidgets));
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [widgets]);

  const saveLayout = useCallback(async (newLayouts) => {
    try {
      // TODO: Remplacer par l'API réelle pour sauvegarder les layouts
      // const response = await fetch('/api/dashboard/layouts/', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(newLayouts)
      // });
      
      setLayouts(newLayouts);
      localStorage.setItem('dashboard-layouts', JSON.stringify(newLayouts));
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const resetToDefault = useCallback(async () => {
    try {
      // TODO: Appel API pour réinitialiser
      localStorage.removeItem('dashboard-widgets');
      localStorage.removeItem('dashboard-layouts');
      setWidgets([]);
      setLayouts({});
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  return {
    widgets,
    layouts,
    loading,
    error,
    fetchWidgets,
    saveWidget,
    updateWidget,
    deleteWidget,
    saveLayout,
    resetToDefault,
    setWidgets,
    setLayouts
  };
};