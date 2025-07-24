import React, { useEffect, useRef, useState } from 'react';

const GoogleLoginPro = ({ onSuccess, onError, disabled = false, text = "signin_with" }) => {
  const googleButtonRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const isInitialized = useRef(false);

  // Configuration depuis les variables d'environnement
  const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  const IS_PRODUCTION = import.meta.env.VITE_ENVIRONMENT === 'production';

  useEffect(() => {
    // Vérifier la configuration
    if (!GOOGLE_CLIENT_ID || GOOGLE_CLIENT_ID === "your-google-client-id.apps.googleusercontent.com") {
      setError("Configuration Google OAuth requise. Consultez GOOGLE_AUTH_PRODUCTION.md");
      return;
    }

    loadGoogleScript();

    return () => {
      // Cleanup
      isInitialized.current = false;
    };
  }, [GOOGLE_CLIENT_ID]);

  const loadGoogleScript = () => {
    // Éviter de charger le script plusieurs fois
    if (window.google || isInitialized.current) {
      initializeGoogleSignIn();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = initializeGoogleSignIn;
    script.onerror = () => {
      setError("Impossible de charger l'API Google. Vérifiez votre connexion internet.");
    };

    document.head.appendChild(script);
  };

  const initializeGoogleSignIn = () => {
    if (!window.google || !googleButtonRef.current || isInitialized.current) {
      return;
    }

    try {
      isInitialized.current = true;

      // Configuration de Google Identity Services
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true,
        use_fedcm_for_prompt: true, // Utiliser FedCM si disponible (plus sécurisé)
      });

      // Rendu du bouton Google
      window.google.accounts.id.renderButton(googleButtonRef.current, {
        theme: 'outline',
        size: 'large',
        width: 400,
        text: text,
        shape: 'rectangular',
        logo_alignment: 'left',
        locale: 'fr', // Français
      });

      // Afficher l'invite de connexion (One Tap) si activé
      if (IS_PRODUCTION) {
        window.google.accounts.id.prompt((notification) => {
          if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
            console.log('Google One Tap not displayed:', notification.getNotDisplayedReason());
          }
        });
      }

    } catch (error) {
      console.error('Erreur lors de l\'initialisation de Google Sign-In:', error);
      setError("Erreur d'initialisation Google OAuth");
      if (onError) onError(error);
    }
  };

  const handleCredentialResponse = async (response) => {
    setIsLoading(true);
    setError(null);

    try {
      // Validation basique du token
      if (!response.credential) {
        throw new Error("Token Google manquant");
      }

      // Décoder le header JWT pour vérification
      const headerB64 = response.credential.split('.')[0];
      const header = JSON.parse(atob(headerB64));
      
      if (header.alg !== 'RS256') {
        throw new Error("Algorithme de signature invalide");
      }

      // Décoder le payload JWT
      const payloadB64 = response.credential.split('.')[1];
      const payload = JSON.parse(atob(payloadB64));

      // Validations de sécurité
      const now = Math.floor(Date.now() / 1000);
      
      if (payload.exp < now) {
        throw new Error("Token Google expiré");
      }

      if (payload.aud !== GOOGLE_CLIENT_ID) {
        throw new Error("Token Google invalide - audience incorrecte");
      }

      if (!['accounts.google.com', 'https://accounts.google.com'].includes(payload.iss)) {
        throw new Error("Token Google invalide - émetteur incorrect");
      }

      // Vérification de l'email
      if (!payload.email_verified) {
        throw new Error("Email Google non vérifié");
      }

      // Construction des informations utilisateur
      const userInfo = {
        credential: response.credential, // Token JWT complet pour validation serveur
        email: payload.email,
        name: payload.name,
        picture: payload.picture,
        sub: payload.sub, // Google ID unique
        given_name: payload.given_name,
        family_name: payload.family_name,
        email_verified: payload.email_verified,
        locale: payload.locale,
        iat: payload.iat,
        exp: payload.exp,
        provider: 'google'
      };

      // Log pour le monitoring (en production, envoyer à votre service de logs)
      console.log('Google Auth Success:', {
        email: userInfo.email,
        timestamp: new Date().toISOString(),
        environment: IS_PRODUCTION ? 'production' : 'development'
      });

      if (onSuccess) {
        await onSuccess(userInfo);
      }

    } catch (error) {
      console.error('Erreur lors du traitement de la réponse Google:', error);
      
      // Log d'erreur pour le monitoring
      console.error('Google Auth Error:', {
        error: error.message,
        timestamp: new Date().toISOString(),
        environment: IS_PRODUCTION ? 'production' : 'development'
      });

      setError(error.message);
      if (onError) onError(error);
      
    } finally {
      setIsLoading(false);
    }
  };

  // Méthode pour déconnecter de Google (appelée lors de la déconnexion)
  const disconnect = () => {
    if (window.google && window.google.accounts && window.google.accounts.id) {
      window.google.accounts.id.disableAutoSelect();
      window.google.accounts.id.revoke(userEmail, (done) => {
        console.log('Google account disconnected');
      });
    }
  };

  // Interface utilisateur
  if (error) {
    return (
      <div className="w-full">
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-red-700 text-sm font-medium">{error}</p>
          </div>
        </div>
        
        {/* Bouton de configuration pour les développeurs */}
        <button
          onClick={() => window.open('/GOOGLE_AUTH_PRODUCTION.md', '_blank')}
          className="w-full text-blue-600 hover:text-blue-800 text-sm underline"
        >
          📖 Voir le guide de configuration
        </button>
      </div>
    );
  }

  return (
    <div className="w-full flex justify-center">
      <div 
        ref={googleButtonRef}
        className={`${disabled || isLoading ? 'opacity-50 pointer-events-none' : ''}`}
      />
      
      {isLoading && (
        <div className="flex items-center justify-center mt-2">
          <svg className="animate-spin h-4 w-4 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span className="text-sm text-gray-600">Connexion en cours...</span>
        </div>
      )}

    </div>
  );
};

// Exposer la méthode de déconnexion
GoogleLoginPro.disconnect = () => {
  if (window.google && window.google.accounts && window.google.accounts.id) {
    window.google.accounts.id.disableAutoSelect();
  }
};

export default GoogleLoginPro;