import React from 'react';

const ToastContainer = ({ toasts, removeToast }) => {
  if (!toasts || toasts.length === 0) return null;

  const getToastStyles = (type) => {
    const baseStyles = "fixed top-4 right-4 max-w-sm w-full p-4 rounded-lg shadow-lg z-50 mb-2";
    
    switch (type) {
      case 'success':
        return `${baseStyles} bg-green-100 border border-green-300 text-green-800`;
      case 'error':
        return `${baseStyles} bg-red-100 border border-red-300 text-red-800`;
      case 'warning':
        return `${baseStyles} bg-yellow-100 border border-yellow-300 text-yellow-800`;
      case 'info':
        return `${baseStyles} bg-blue-100 border border-blue-300 text-blue-800`;
      default:
        return `${baseStyles} bg-gray-100 border border-gray-300 text-gray-800`;
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map((toast, index) => (
        <div
          key={toast.id}
          className={getToastStyles(toast.type)}
          style={{ top: `${4 + index * 80}px` }}
        >
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <h4 className="font-semibold text-sm">{toast.title}</h4>
              {toast.message && (
                <p className="text-sm mt-1">{toast.message}</p>
              )}
            </div>
            <button
              onClick={() => removeToast(toast.id)}
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

export default ToastContainer;