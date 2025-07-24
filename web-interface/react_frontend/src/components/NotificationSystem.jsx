import React, { useState, useCallback, createContext, useContext } from 'react';

const NotificationContext = createContext();

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);

  const addNotification = useCallback((type, title, message) => {
    const id = Date.now() + Math.random();
    const notification = {
      id,
      type,
      title,
      message,
      timestamp: new Date()
    };

    setNotifications(prev => [...prev, notification]);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);

    return id;
  }, []);

  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const success = useCallback((title, message) => {
    return addNotification('success', title, message);
  }, [addNotification]);

  const error = useCallback((title, message) => {
    return addNotification('error', title, message);
  }, [addNotification]);

  const loading = useCallback((title, message) => {
    return addNotification('loading', title, message);
  }, [addNotification]);

  const value = {
    notifications,
    success,
    error,
    loading,
    removeNotification
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <NotificationContainer notifications={notifications} removeNotification={removeNotification} />
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

const NotificationContainer = ({ notifications, removeNotification }) => {
  if (!notifications || notifications.length === 0) return null;

  const getNotificationStyles = (type) => {
    const baseStyles = "fixed top-4 right-4 max-w-sm w-full p-4 rounded-lg shadow-lg z-50 mb-2";
    
    switch (type) {
      case 'success':
        return `${baseStyles} bg-green-100 border border-green-300 text-green-800`;
      case 'error':
        return `${baseStyles} bg-red-100 border border-red-300 text-red-800`;
      case 'loading':
        return `${baseStyles} bg-blue-100 border border-blue-300 text-blue-800`;
      default:
        return `${baseStyles} bg-gray-100 border border-gray-300 text-gray-800`;
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map((notification, index) => (
        <div
          key={notification.id}
          className={getNotificationStyles(notification.type)}
          style={{ top: `${4 + index * 80}px` }}
        >
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <h4 className="font-semibold text-sm">{notification.title}</h4>
              {notification.message && (
                <p className="text-sm mt-1">{notification.message}</p>
              )}
            </div>
            <button
              onClick={() => removeNotification(notification.id)}
              className="ml-4 text-lg font-bold opacity-70 hover:opacity-100"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};