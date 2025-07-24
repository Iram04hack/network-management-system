import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import HYBRIDOLogo from '../assets/logo.png';
import GoogleLoginPro from '../components/GoogleLoginPro';
import LoadingSpinner from '../components/LoadingSpinner';
import ToastContainer from '../components/ToastContainer';
import { useGoogleAuthPro } from '../hooks/useGoogleAuthPro';
import { useToast } from '../hooks/useToast';
import { useTheme } from '../contexts/ThemeContext';
import { useNotifications } from '../components/NotificationSystem';
import sessionService from '../services/sessionService';
import credentialService from '../services/credentialService';

const Register = () => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    company: '',
    agreeTerms: false
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [touchedFields, setTouchedFields] = useState({});
  const navigate = useNavigate();
  
  // Hooks  
  const { toasts, success: toastSuccess, error: toastError, removeToast } = useToast();
  const { getThemeClasses } = useTheme();
  const { success, error: showError, loading } = useNotifications();
  const { 
    handleGoogleSuccess, 
    handleGoogleError, 
    isLoading: googleLoading, 
    error: googleError 
  } = useGoogleAuthPro();

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Marquer le champ comme touché
    setTouchedFields(prev => ({ ...prev, [name]: true }));
    
    // Effacer l'erreur du champ modifié
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleBlur = (e) => {
    const { name } = e.target;
    setTouchedFields(prev => ({ ...prev, [name]: true }));
    
    // Validation en temps réel sur blur
    validateField(name, formData[name]);
  };

  const validateField = (fieldName, value) => {
    const newErrors = { ...errors };
    
    switch (fieldName) {
      case 'email':
        if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          newErrors.email = 'Format d\'email invalide';
        } else {
          delete newErrors.email;
        }
        break;
      case 'password':
        if (value && value.length < 8) {
          newErrors.password = 'Au moins 8 caractères requis';
        } else {
          delete newErrors.password;
        }
        break;
      case 'confirmPassword':
        if (value && value !== formData.password) {
          newErrors.confirmPassword = 'Les mots de passe ne correspondent pas';
        } else {
          delete newErrors.confirmPassword;
        }
        break;
    }
    
    setErrors(newErrors);
  };

  const validateForm = () => {
    const newErrors = {};
    
    // Validation des champs obligatoires
    if (!formData.firstName.trim()) newErrors.firstName = 'Le prénom est requis';
    if (!formData.lastName.trim()) newErrors.lastName = 'Le nom est requis';
    if (!formData.email.trim()) newErrors.email = 'L\'email est requis';
    if (!formData.password) newErrors.password = 'Le mot de passe est requis';
    if (!formData.confirmPassword) newErrors.confirmPassword = 'Confirmez votre mot de passe';
    if (!formData.agreeTerms) newErrors.agreeTerms = 'Vous devez accepter les conditions';
    
    // Validation de l'email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (formData.email && !emailRegex.test(formData.email)) {
      newErrors.email = 'Email invalide';
    }
    
    // Validation du mot de passe
    if (formData.password && formData.password.length < 8) {
      newErrors.password = 'Le mot de passe doit contenir au moins 8 caractères';
    }
    
    // Confirmation du mot de passe
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Les mots de passe ne correspondent pas';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsLoading(true);
    
    try {
      // Notification de chargement
      const loadingId = loading('Inscription', 'Création de votre compte en cours...');
      
      // Simuler la création de compte (remplacer par votre API)
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Créer les données utilisateur
      const userData = {
        email: formData.email,
        firstName: formData.firstName,
        lastName: formData.lastName,
        name: `${formData.firstName} ${formData.lastName}`,
        company: formData.company || null,
        provider: 'local',
        role: formData.company ? 'Administrateur' : 'Utilisateur',
        emailVerified: false
      };
      
      // Utiliser le service de session pour gérer les données
      sessionService.setSessionData(userData, false);
      localStorage.setItem('auth_token', 'demo_token');
      
      // Marquer que l'utilisateur s'est inscrit et sauvegarder les identifiants
      credentialService.markAsRegistered();
      credentialService.saveCredentials(formData.email, true); // Auto-remember pour les nouvelles inscriptions
      
      console.log('✅ Compte créé avec succès:', userData);
      
      // Notification de succès
      success('Compte créé !', `Bienvenue ${formData.firstName} ! Votre compte a été créé avec succès.`);
      
      // Petit délai pour voir la notification
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);
      
    } catch (err) {
      console.error('Erreur lors de la création du compte:', err);
      showError('Erreur d\'inscription', 'Erreur lors de la création du compte. Veuillez réessayer.');
      setErrors({ submit: 'Erreur lors de la création du compte. Veuillez réessayer.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`${getThemeClasses('background', 'auth')} flex items-center justify-center p-4`}>
      <div className="flex items-center justify-center w-full h-full">
        <div className={`${getThemeClasses('container', 'auth')} p-8 w-full max-w-2xl mx-auto`}>
          
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex justify-center mb-6">
              <img src={HYBRIDOLogo} alt="HYBRIDO" className="h-16 object-contain" />
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">Créer votre compte</h1>
            <p className="text-gray-300">Rejoignez-nous pour gérer votre réseau efficacement</p>
          </div>

          {/* Formulaire */}
          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Prénom et Nom */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Prénom *
                </label>
                <input
                  type="text"
                  name="firstName"
                  value={formData.firstName}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  className={`w-full px-4 py-3 border rounded-lg text-gray-300 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all duration-200 ${
                    errors.firstName ? 'border-red-500 focus:ring-red-500' : 
                    touchedFields.firstName && formData.firstName ? 'border-green-500 focus:ring-green-500' : 'border-gray-600'
                  }`}
                  placeholder="Votre prénom"
                />
                {errors.firstName && <p className="text-red-500 text-sm mt-1">{errors.firstName}</p>}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Nom *
                </label>
                <input
                  type="text"
                  name="lastName"
                  value={formData.lastName}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 border rounded-lg text-gray-300 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all duration-200 ${
                    errors.lastName ? 'border-red-500' : 'border-gray-600'
                  }`}
                  placeholder="Votre nom"
                />
                {errors.lastName && <p className="text-red-500 text-sm mt-1">{errors.lastName}</p>}
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Adresse email *
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`w-full px-4 py-3 border rounded-lg text-gray-300 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all duration-200 ${
                  errors.email ? 'border-red-500' : 'border-gray-600'
                }`}
                placeholder="votre.email@exemple.com"
              />
              {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email}</p>}
            </div>

            {/* Entreprise */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Entreprise (optionnel)
              </label>
              <input
                type="text"
                name="company"
                value={formData.company}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-600 rounded-lg text-gray-300 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all duration-200"
                placeholder="Nom de votre entreprise"
              />
            </div>

            {/* Mots de passe */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Mot de passe *
                </label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 border rounded-lg text-gray-300 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all duration-200 ${
                    errors.password ? 'border-red-500' : 'border-gray-600'
                  }`}
                  placeholder="8+ caractères"
                />
                {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password}</p>}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Confirmer le mot de passe *
                </label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className={`w-full px-4 py-3 border rounded-lg text-gray-300 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all duration-200 ${
                    errors.confirmPassword ? 'border-red-500' : 'border-gray-600'
                  }`}
                  placeholder="Répétez le mot de passe"
                />
                {errors.confirmPassword && <p className="text-red-500 text-sm mt-1">{errors.confirmPassword}</p>}
              </div>
            </div>

            {/* Conditions d'utilisation */}
            <div className="flex items-start space-x-3">
              <input
                type="checkbox"
                name="agreeTerms"
                checked={formData.agreeTerms}
                onChange={handleChange}
                className="mt-1 h-4 w-4 text-blue-600 border-gray-600 rounded focus:ring-2 focus:ring-blue-400"
              />
              <label className="text-sm text-gray-300">
                J'accepte les{' '}
                <Link to="/terms" className="text-blue-400 hover:text-blue-300 underline">
                  conditions d'utilisation
                </Link>{' '}
                et la{' '}
                <Link to="/privacy" className="text-blue-400 hover:text-blue-300 underline">
                  politique de confidentialité
                </Link>
              </label>
            </div>
            {errors.agreeTerms && <p className="text-red-500 text-sm">{errors.agreeTerms}</p>}

            {/* Erreur générale */}
            {errors.submit && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-red-600 text-sm font-medium">{errors.submit}</p>
              </div>
            )}

            {/* Bouton de création */}
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
                <span className="flex items-center space-x-3">
                  <div className="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span>Création en cours...</span>
                </span>
              ) : (
                <>
                  <span className="mr-2">✨</span>
                  Créer mon compte
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-600"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gray-700 text-gray-400">ou</span>
            </div>
          </div>

          {/* Google Login */}
          <div className="mb-6">
            <GoogleLoginPro
              onSuccess={handleGoogleSuccess}
              onError={handleGoogleError}
              disabled={googleLoading}
              text="signup_with"
            />
            {googleError && (
              <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="text-red-700 text-sm font-medium">{googleError}</p>
                </div>
              </div>
            )}
          </div>

          {/* Lien vers connexion */}
          <div className="text-center pt-6 border-t border-gray-700">
            <p className="text-gray-300">
              Vous avez déjà un compte ?{' '}
              <Link 
                to="/login" 
                className="text-blue-400 hover:text-blue-300 font-semibold underline transition-colors duration-200"
              >
                Se connecter
              </Link>
            </p>
          </div>
        </div>
      </div>
      
      {/* Container pour les toasts */}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </div>
  );
};

export default Register;