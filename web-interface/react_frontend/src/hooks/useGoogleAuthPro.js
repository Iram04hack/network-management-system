import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import sessionService from '../services/sessionService';

export const useGoogleAuthPro = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // Configuration
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const IS_PRODUCTION = import.meta.env.VITE_ENVIRONMENT === 'production';

  const handleGoogleSuccess = useCallback(async (userInfo) => {
    setIsLoading(true);
    setError(null);

    try {
      // Log de tentative de connexion
      console.log('Début de l\'authentification Google:', {
        email: userInfo.email,
        timestamp: new Date().toISOString()
      });

      // Validation côté serveur (recommandé pour la production)
      if (IS_PRODUCTION) {
        const response = await fetch(`${API_URL}/api/auth/google/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: JSON.stringify({
            credential: userInfo.credential,
            client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Erreur de validation serveur');
        }

        const serverData = await response.json();
        
        // Utiliser les données validées par le serveur
        const validatedUserInfo = {
          ...userInfo,
          serverToken: serverData.token,
          permissions: serverData.permissions || [],
          lastLogin: new Date().toISOString()
        };

        await saveAuthData(validatedUserInfo);
        
      } else {
        // Mode développement - validation côté client uniquement
        await saveAuthData(userInfo);
      }

      // Log de succès
      console.log('Authentification Google réussie:', {
        email: userInfo.email,
        provider: 'google',
        timestamp: new Date().toISOString(),
        environment: IS_PRODUCTION ? 'production' : 'development'
      });

      // Redirection immédiate après sauvegarde
      console.log('🚀 Redirection vers /dashboard...');
      navigate('/dashboard', { replace: true });
      
    } catch (err) {
      console.error('Erreur lors de l\'authentification Google:', err);
      
      // Log d'erreur pour le monitoring
      console.error('Google Auth Error:', {
        error: err.message,
        email: userInfo?.email,
        timestamp: new Date().toISOString(),
        environment: IS_PRODUCTION ? 'production' : 'development'
      });

      setError(getHumanReadableError(err.message));
      
      // Nettoyage en cas d'erreur
      cleanAuthData();
      
    } finally {
      setIsLoading(false);
    }
  }, [navigate, API_URL, IS_PRODUCTION]);

  const handleGoogleError = useCallback((error) => {
    console.error('Erreur Google Identity Services:', error);
    
    let errorMessage = 'Erreur de connexion avec Google';
    
    // Gestion des erreurs spécifiques
    if (error.message?.includes('popup_closed_by_user')) {
      errorMessage = 'Connexion annulée par l\'utilisateur';
    } else if (error.message?.includes('access_denied')) {
      errorMessage = 'Accès refusé par Google';
    } else if (error.message?.includes('network')) {
      errorMessage = 'Erreur de connexion réseau';
    }
    
    setError(errorMessage);
    setIsLoading(false);
  }, []);

  const logout = useCallback(async () => {
    setIsLoading(true);
    
    try {
      // Déconnexion côté serveur si en production
      if (IS_PRODUCTION) {
        const token = localStorage.getItem('auth_token');
        if (token) {
          await fetch(`${API_URL}/api/auth/logout/`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
        }
      }

      // Déconnexion Google
      if (window.google && window.google.accounts && window.google.accounts.id) {
        window.google.accounts.id.disableAutoSelect();
      }

      // Nettoyage local
      cleanAuthData();

      // Log de déconnexion
      console.log('Déconnexion réussie:', {
        timestamp: new Date().toISOString(),
        environment: IS_PRODUCTION ? 'production' : 'development'
      });

      navigate('/');
      
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
      
      // Forcer le nettoyage même en cas d'erreur
      cleanAuthData();
      navigate('/');
      
    } finally {
      setIsLoading(false);
    }
  }, [navigate, API_URL, IS_PRODUCTION]);

  // Fonctions utilitaires
  const saveAuthData = async (userInfo) => {
    try {
      console.log('🔍 Debug saveAuthData - userInfo reçu:', userInfo);
      
      // Token d'authentification - plus robuste
      const userId = userInfo.sub || userInfo.email?.split('@')[0] || 'user';
      const authToken = userInfo.serverToken || `google_${userId}_${Date.now()}`;
      
      console.log('🔑 Token généré:', authToken);
      localStorage.setItem('auth_token', authToken);

      // Informations utilisateur Google
      const userData = {
        email: userInfo.email,
        name: userInfo.name,
        picture: userInfo.picture,
        provider: 'google',
        permissions: userInfo.permissions || [],
        emailVerified: userInfo.email_verified || false,
        sub: userInfo.sub // ID Google unique
      };

      // Utiliser le service de session
      sessionService.setSessionData(userData, true); // true pour "se souvenir"

      // Métadonnées de session
      const sessionData = {
        loginMethod: 'google',
        sessionStart: new Date().toISOString(),
        lastHeartbeat: new Date().toISOString(),
        environment: IS_PRODUCTION ? 'production' : 'development'
      };

      localStorage.setItem('session_info', JSON.stringify(sessionData));

      // Vérification immédiate de la sauvegarde
      const savedToken = localStorage.getItem('auth_token');
      const savedUser = localStorage.getItem('user_info');
      console.log('✅ Vérification sauvegarde immédiate:', {
        tokenSaved: !!savedToken,
        userSaved: !!savedUser,
        tokenValue: savedToken
      });

    } catch (error) {
      console.error('Erreur lors de la sauvegarde des données d\'auth:', error);
      throw new Error('Erreur de sauvegarde des données de session');
    }
  };

  const cleanAuthData = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    localStorage.removeItem('session_info');
    localStorage.removeItem('remember_user');
  };

  const getHumanReadableError = (errorMessage) => {
    const errorMap = {
      'Token Google expiré': 'Votre session Google a expiré. Veuillez vous reconnecter.',
      'Token Google invalide': 'Erreur d\'authentification Google. Veuillez réessayer.',
      'Email Google non vérifié': 'Votre email Google doit être vérifié pour vous connecter.',
      'Erreur de validation serveur': 'Erreur de connexion au serveur. Veuillez réessayer.',
      'Configuration Google OAuth requise': 'Configuration Google manquante. Contactez l\'administrateur.',
    };

    return errorMap[errorMessage] || errorMessage || 'Erreur de connexion inconnue';
  };

  // Fonction pour vérifier si l'utilisateur est connecté
  const isAuthenticated = useCallback(() => {
    const token = localStorage.getItem('auth_token');
    const userInfo = localStorage.getItem('user_info');
    return !!(token && userInfo);
  }, []);

  // Fonction pour obtenir les infos utilisateur actuelles
  const getCurrentUser = useCallback(() => {
    try {
      const userInfo = localStorage.getItem('user_info');
      return userInfo ? JSON.parse(userInfo) : null;
    } catch (error) {
      console.error('Erreur lors de la récupération des infos utilisateur:', error);
      return null;
    }
  }, []);

  // Fonction pour rafraîchir le heartbeat de session
  const refreshSession = useCallback(() => {
    try {
      const sessionInfo = localStorage.getItem('session_info');
      if (sessionInfo) {
        const session = JSON.parse(sessionInfo);
        session.lastHeartbeat = new Date().toISOString();
        localStorage.setItem('session_info', JSON.stringify(session));
      }
    } catch (error) {
      console.error('Erreur lors du rafraîchissement de session:', error);
    }
  }, []);

  return {
    handleGoogleSuccess,
    handleGoogleError,
    logout,
    isLoading,
    error,
    setError,
    isAuthenticated,
    getCurrentUser,
    refreshSession
  };
};