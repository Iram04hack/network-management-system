import { useState, useCallback } from 'react';

export const useToast = () => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((type, title, message) => {
    const id = Date.now() + Math.random();
    const toast = {
      id,
      type,
      title,
      message,
      timestamp: new Date()
    };

    setToasts(prev => [...prev, toast]);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 5000);

    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const success = useCallback((title, message) => {
    return addToast('success', title, message);
  }, [addToast]);

  const error = useCallback((title, message) => {
    return addToast('error', title, message);
  }, [addToast]);

  const warning = useCallback((title, message) => {
    return addToast('warning', title, message);
  }, [addToast]);

  const info = useCallback((title, message) => {
    return addToast('info', title, message);
  }, [addToast]);

  return {
    toasts,
    success,
    error,
    warning,
    info,
    removeToast
  };
};