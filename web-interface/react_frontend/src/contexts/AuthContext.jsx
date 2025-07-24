import React, { createContext, useState, useEffect, useContext } from 'react';

// Créer le contexte d'authentification
const AuthContext = createContext(null);

// Provider component - COMPOSANT PRINCIPAL du fichier
function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is authenticated on initial load
    const token = localStorage.getItem('auth_token');
    if (token) {
      setIsAuthenticated(true);
      setUser({ email: localStorage.getItem('remember_user') || 'admin@hybrido.com' });
    }
    setLoading(false);
  }, []);

  const login = (email, password, rememberMe = false) => {
    // Simulation de l'authentification
    if (email && password) {
      setIsAuthenticated(true);
      setUser({ email });
      
      // Stocker le token d'authentification
      localStorage.setItem('auth_token', 'dummy_token_' + Date.now());
      
      // Stocker l'email si "Se souvenir de moi" est coché
      if (rememberMe) {
        localStorage.setItem('remember_user', email);
      } else {
        localStorage.removeItem('remember_user');
      }
      
      return true;
    }
    return false;
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('auth_token');
  };

  const value = {
    isAuthenticated,
    user,
    login,
    logout,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook personnalisé attaché au composant
AuthProvider.useAuth = function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Export UNIQUEMENT le composant
export default AuthProvider;