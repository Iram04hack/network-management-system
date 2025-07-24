import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import HYBRIDOLogo from '../assets/logo.png';
import GoogleLoginPro from '../components/GoogleLoginPro';
import { useGoogleAuthPro } from '../hooks/useGoogleAuthPro';
import { useTheme } from '../contexts/ThemeContext';
import { useNotifications } from '../components/NotificationSystem';
import credentialService from '../services/credentialService';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [emailSuggestions, setEmailSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [inputErrors, setInputErrors] = useState({});
  const navigate = useNavigate();
  
  // Hook pour le thème et notifications
  const { getThemeClasses, getThemeColor } = useTheme();
  const { success, error: showError, loading } = useNotifications();
  
  // Hook pour l'authentification Google professionnelle
  const { 
    handleGoogleSuccess, 
    handleGoogleError, 
    isLoading: googleLoading, 
    error: googleError 
  } = useGoogleAuthPro();

  // Wrapper pour Google Success avec intégration credentialService
  const handleGoogleLogin = async (userInfo) => {
    try {
      // Sauvegarder automatiquement les identifiants Google
      credentialService.saveCredentials(userInfo.email, true);
      credentialService.markAsRegistered();
      
      // Continuer avec le processus normal
      await handleGoogleSuccess(userInfo);
    } catch (error) {
      console.error('Erreur lors de la connexion Google:', error);
      handleGoogleError(error);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setInputErrors({});
    setIsLoading(true);

    // Notification de chargement
    const loadingId = loading('Connexion', 'Vérification des identifiants...');

    try {
      // Vérifier si le compte est verrouillé
      const lockStatus = credentialService.isAccountLocked(email);
      if (lockStatus.locked) {
        const errorMsg = `Compte temporairement verrouillé. Réessayez dans ${lockStatus.minutesRemaining} minutes.`;
        setError(errorMsg);
        showError('Compte verrouillé', errorMsg);
        // Animation d'erreur sur les champs
        setInputErrors({ email: 'error', password: 'error' });
        return;
      }

      // Simulation de délai réseau
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Simulation de la connexion (remplacer par votre API)
      if (email === 'admin@hybrido.com' && password === 'hybrido2025') {
        // Connexion réussie
        localStorage.setItem('auth_token', 'demo_token');
        
        // Sauvegarder les identifiants
        credentialService.saveCredentials(email, rememberMe);
        
        // Animations de succès
        setInputErrors({ email: 'success', password: 'success' });
        success('Connexion réussie', `Bienvenue ${email} !`);
        
        console.log('✅ Connexion réussie');
        
        // Délai pour voir l'animation de succès
        setTimeout(() => {
          navigate('/dashboard');
        }, 1000);
      } else {
        // Connexion échouée
        const attemptCount = credentialService.recordFailedAttempt(email);
        const remaining = credentialService.MAX_LOGIN_ATTEMPTS - attemptCount;
        
        let errorMsg;
        if (remaining > 0) {
          errorMsg = `Identifiants incorrects. ${remaining} tentative(s) restante(s).`;
        } else {
          errorMsg = `Trop de tentatives. Compte verrouillé pendant 15 minutes.`;
        }
        
        setError(errorMsg);
        showError('Échec de connexion', errorMsg);
        
        // Animation d'erreur sur les champs
        setInputErrors({ email: 'error', password: 'error' });
      }
    } catch (err) {
      console.error('Erreur de connexion:', err);
      showError('Erreur', 'Une erreur inattendue s\'est produite');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    localStorage.removeItem('remember_user');
    window.location.reload();
  };

  // Vérifier si l'utilisateur est connecté SANS redirection automatique
  const [isLoggedIn, setIsLoggedIn] = React.useState(false);
  
  React.useEffect(() => {
    const initializeLogin = () => {
      // Vérifier l'authentification
      const token = localStorage.getItem('auth_token');
      const userInfo = localStorage.getItem('user_info');
      const isAuthenticated = !!(token && userInfo);
      
      if (isAuthenticated && window.location.pathname === '/') {
        console.log('✅ Utilisateur authentifié détecté, redirection...');
        navigate('/dashboard', { replace: true });
        return true;
      }
      
      setIsLoggedIn(isAuthenticated);

      // Charger les identifiants sauvegardés
      const savedCreds = credentialService.getSavedCredentials();
      if (savedCreds) {
        setEmail(savedCreds.email);
        setRememberMe(savedCreds.rememberMe);
        console.log('🔄 Identifiants chargés:', savedCreds.email);
      }
      
      return false;
    };
    
    // Initialisation
    if (initializeLogin()) return;
    
    // Vérifier seulement si on est sur la page de login
    if (window.location.pathname !== '/') return;
    
    // Vérifier moins fréquemment et arrêter plus tôt
    let checkCount = 0;
    const interval = setInterval(() => {
      checkCount++;
      if (checkCount >= 10) { // Arrêter après 1 seconde
        clearInterval(interval);
      }
    }, 100);
    
    return () => {
      clearInterval(interval);
    };
  }, [navigate]);
  
  if (isLoggedIn) {
    return (
      <div className="min-h-screen w-full bg-gray-200 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md mx-auto text-center">
          <h2 className="text-xl font-semibold mb-4">Déjà connecté</h2>
          <p className="text-gray-600 mb-6">Vous êtes déjà connecté au système.</p>
          <div className="space-y-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white py-3 rounded-lg font-semibold"
            >
              Aller au Dashboard
            </button>
            <button
              onClick={handleLogout}
              className="w-full bg-gray-500 hover:bg-gray-600 text-white py-3 rounded-lg font-semibold"
            >
              Se déconnecter
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${getThemeClasses('background', 'auth')} flex items-center justify-center p-4`}>
      <div className="flex items-center justify-center w-full h-full">
        <div className={`${getThemeClasses('container', 'auth')} p-8 w-full max-w-md mx-auto`}>
          {/* Logo Header */}
          <div className="flex justify-center mb-8">
            <img src={HYBRIDOLogo} alt="HYBRIDO" className="h-20 object-contain" />
          </div>
          
          {/* Login Form */}
          <form onSubmit={handleLogin} className="space-y-6">
            {/* Email Input avec suggestions */}
            <div className="relative">
              <input
                type="email"
                className={`
                  w-full px-4 py-3 border border-gray-600 bg-gray-700 rounded-lg text-white placeholder-gray-400 
                  focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent 
                  input-animate transition-smooth text-base
                  ${inputErrors.email === 'error' ? 'input-error' : ''}
                  ${inputErrors.email === 'success' ? 'input-success' : ''}
                `}
                placeholder="Nom d'utilisateur / Email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  // Générer des suggestions basées sur la saisie
                  if (e.target.value.length > 0) {
                    const suggestions = credentialService.getEmailSuggestions(e.target.value);
                    setEmailSuggestions(suggestions);
                    setShowSuggestions(suggestions.length > 0);
                  } else {
                    setShowSuggestions(false);
                  }
                }}
                onFocus={() => {
                  if (email.length > 0) {
                    const suggestions = credentialService.getEmailSuggestions(email);
                    setEmailSuggestions(suggestions);
                    setShowSuggestions(suggestions.length > 0);
                  }
                }}
                onBlur={() => {
                  // Délai pour permettre le clic sur les suggestions
                  setTimeout(() => setShowSuggestions(false), 200);
                }}
                required
              />
              
              {/* Suggestions dropdown */}
              {showSuggestions && emailSuggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg">
                  {emailSuggestions.map((suggestion, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => {
                        setEmail(suggestion.email);
                        setShowSuggestions(false);
                      }}
                      className="w-full px-4 py-2 text-left hover:bg-blue-50 focus:bg-blue-50 focus:outline-none transition-colors duration-150 first:rounded-t-lg last:rounded-b-lg"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-gray-900">{suggestion.email}</span>
                        <span className="text-xs text-blue-600">
                          {suggestion.type === 'saved' ? '💾 Mémorisé' : 
                           suggestion.type === 'demo' ? '🧪 Demo' : ''}
                        </span>
                      </div>
                      {suggestion.lastLogin && (
                        <div className="text-xs text-gray-400 mt-1">
                          Dernière connexion: {new Date(suggestion.lastLogin).toLocaleDateString('fr-FR')}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Password Input */}
            <div>
              <input
                type="password"
                className={`
                  w-full px-4 py-3 border border-gray-600 bg-gray-700 rounded-lg text-white placeholder-gray-400 
                  focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent 
                  input-animate transition-smooth text-base
                  ${inputErrors.password === 'error' ? 'input-error' : ''}
                  ${inputErrors.password === 'success' ? 'input-success' : ''}
                `}
                placeholder="Mot de passe"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {/* Remember Me Checkbox */}
            <div className="flex items-center">
              <input
                id="remember-me"
                type="checkbox"
                className="h-4 w-4 text-blue-400 bg-gray-700 border-gray-600 rounded focus:ring-2 focus:ring-blue-400"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              <label htmlFor="remember-me" className="ml-3 text-sm text-gray-300 font-medium">
                Remember me
              </label>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-900 border border-red-700 rounded-lg p-3">
                <p className="text-red-300 text-sm font-medium">{error}</p>
              </div>
            )}

            {/* Login Button */}
            <button
              type="submit"
              disabled={isLoading}
              className={`
                w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed
                text-white py-3 rounded-lg font-semibold text-base 
                flex items-center justify-center 
                btn-animate transition-smooth shadow-md hover:shadow-lg
                ${isLoading ? 'btn-pulse' : ''}
              `}
            >
              {isLoading ? (
                <>
                  <div className="loading-dots mr-2">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  Connexion...
                </>
              ) : (
                <>
                  <span className="mr-2 text-lg">→</span>
                  Login
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-600"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gray-800 text-gray-400">ou</span>
            </div>
          </div>

          {/* Google Login Button Professional */}
          <div className="mb-6">
            <GoogleLoginPro
              onSuccess={handleGoogleLogin}
              onError={handleGoogleError}
              disabled={googleLoading}
              text="signin_with"
            />
            {googleError && (
              <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="text-red-700 text-sm font-medium">{googleError}</p>
                    <p className="text-red-600 text-xs mt-1">
                      Problème de connexion Google. Essayez la connexion classique ci-dessus.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Indicateur de chargement Google */}
            {googleLoading && (
              <div className="mt-3 flex items-center justify-center">
                <div className="flex items-center space-x-2 text-blue-600">
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span className="text-sm">Connexion Google en cours...</span>
                </div>
              </div>
            )}
          </div>

          {/* Lien vers inscription */}
          <div className="text-center pt-6 border-t border-gray-700">
            <p className="text-gray-300">
              Pas encore de compte ?{' '}
              <Link 
                to="/register" 
                className="text-blue-400 hover:text-blue-300 font-semibold underline transition-colors duration-200"
              >
                Créer un compte
              </Link>
            </p>
          </div>

          {/* Warning Text */}
          <div className="mt-6">
            <p className="text-xs text-center text-gray-400 leading-relaxed">
              L'accès ou l'utilisation non autorisés rendent l'utilisateur<br />
              passible de poursuites pénales et/ou civiles.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;