/**
 * Utility pour gérer l'authentification avec le backend Django
 * Simplifié pour les tests d'intégration
 */

const AUTH_CONFIG = {
  baseURL: 'http://localhost:8000',
  loginEndpoint: '/api/auth/login/',
  logoutEndpoint: '/api/auth/logout/',
  refreshEndpoint: '/api/auth/refresh/',
  
  // Credentials par défaut pour les tests
  defaultCredentials: {
    username: 'admin',
    password: 'admin123'
  }
};

class AuthService {
  constructor() {
    this.token = localStorage.getItem('auth_token');
    this.user = this.getStoredUser();
  }

  getStoredUser() {
    try {
      const userStr = localStorage.getItem('auth_user');
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  setUser(user) {
    this.user = user;
    if (user) {
      localStorage.setItem('auth_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('auth_user');
    }
  }

  getAuthHeaders() {
    if (this.token) {
      return {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      };
    }
    return {
      'Content-Type': 'application/json'
    };
  }

  async login(username = null, password = null) {
    try {
      // Utiliser les credentials par défaut si non fournis
      const credentials = {
        username: username || AUTH_CONFIG.defaultCredentials.username,
        password: password || AUTH_CONFIG.defaultCredentials.password
      };

      const response = await fetch(`${AUTH_CONFIG.baseURL}${AUTH_CONFIG.loginEndpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(credentials)
      });

      if (response.ok) {
        const data = await response.json();
        this.setToken(data.token || data.access_token || data.key);
        this.setUser(data.user || { username: credentials.username });
        return { success: true, data };
      } else {
        // Si l'authentification échoue, on continue sans token pour les APIs publiques
        console.warn('Auth failed, continuing without token for public APIs');
        return { success: false, error: 'Authentication failed' };
      }
    } catch (error) {
      console.warn('Auth service not available, continuing without token');
      return { success: false, error: error.message };
    }
  }

  async logout() {
    try {
      if (this.token) {
        await fetch(`${AUTH_CONFIG.baseURL}${AUTH_CONFIG.logoutEndpoint}`, {
          method: 'POST',
          headers: this.getAuthHeaders()
        });
      }
    } catch (error) {
      console.warn('Logout request failed:', error);
    } finally {
      this.setToken(null);
      this.setUser(null);
    }
  }

  isAuthenticated() {
    return !!this.token && !!this.user;
  }

  getToken() {
    return this.token;
  }

  getUser() {
    return this.user;
  }

  async autoLogin() {
    if (!this.isAuthenticated()) {
      const result = await this.login();
      return result.success;
    }
    return true;
  }
}

// Instance globale
const authService = new AuthService();

// Hook React pour l'authentification
export const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = React.useState(authService.isAuthenticated());
  const [user, setUser] = React.useState(authService.getUser());
  const [loading, setLoading] = React.useState(false);

  const login = async (username, password) => {
    setLoading(true);
    try {
      const result = await authService.login(username, password);
      setIsAuthenticated(authService.isAuthenticated());
      setUser(authService.getUser());
      return result;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await authService.logout();
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const autoLogin = async () => {
    setLoading(true);
    try {
      const success = await authService.autoLogin();
      setIsAuthenticated(authService.isAuthenticated());
      setUser(authService.getUser());
      return success;
    } finally {
      setLoading(false);
    }
  };

  return {
    isAuthenticated,
    user,
    loading,
    login,
    logout,
    autoLogin,
    getAuthHeaders: () => authService.getAuthHeaders()
  };
};

export default authService;