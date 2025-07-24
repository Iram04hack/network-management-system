import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import LoadingSpinner from '../components/LoadingSpinner';
import { useTheme } from '../contexts/ThemeContext';
import sessionService from '../services/sessionService';
import welcomeMessageService from '../services/welcomeMessageService';
import firstVisitService from '../services/firstVisitService';
import '../styles/welcome-animations.css';

const Welcome = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [currentText, setCurrentText] = useState('');
  const [welcomeData, setWelcomeData] = useState(null);
  const navigate = useNavigate();
  const { getThemeClasses } = useTheme();
  
  useEffect(() => {
    // Marquer cette visite
    firstVisitService.markVisit('anonymous');
    
    // Obtenir les données de bienvenue
    const welcomeMessage = welcomeMessageService.getWelcomeMessage();
    setWelcomeData(welcomeMessage);
    
    // Animation d'apparition
    setTimeout(() => setIsVisible(true), 300);
    
    // Animation de typing plus rapide
    let index = 0;
    const fullText = welcomeMessage.main;
    const typeInterval = setInterval(() => {
      if (index < fullText.length) {
        setCurrentText(fullText.slice(0, index + 1));
        index++;
      } else {
        clearInterval(typeInterval);
        // Auto-redirection après 5 secondes
        setTimeout(() => {
          handleAutoRedirect();
        }, 5000);
      }
    }, 80); // Réglage vitesse typing
    
    return () => clearInterval(typeInterval);
  }, []);

  const handleAutoRedirect = () => {
    // Vérifier si utilisateur connecté
    const token = localStorage.getItem('auth_token');
    const isSessionValid = sessionService.isSessionValid();
    
    if (token && isSessionValid) {
      console.log('➡️ Utilisateur connecté → Dashboard');
      navigate('/dashboard');
      return;
    }
    
    // Vérifier si c'est vraiment la première visite
    const isFirstVisit = firstVisitService.isFirstVisit();
    const visitStats = firstVisitService.getVisitStats();
    const hasEverRegistered = localStorage.getItem('has_registered') === 'true';
    const rememberUser = localStorage.getItem('remember_user');
    
    // Logique de redirection intelligente
    if (isFirstVisit && !hasEverRegistered && !rememberUser) {
      console.log('➡️ Nouvelle utilisateur → Inscription');
      navigate('/register');
    } else {
      console.log('➡️ Utilisateur de retour → Connexion');
      navigate('/login');
    }
  };
  
  
  return (
    <div 
      className={`${getThemeClasses('background', 'dashboard')} flex items-center justify-center relative overflow-hidden`}
      role="main"
      aria-labelledby="welcome-title"
    >
      {/* Arrière-plan minimal */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-blue-200 rounded-full opacity-10 animate-pulse blur-xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-40 h-40 bg-indigo-200 rounded-full opacity-10 animate-pulse blur-2xl" style={{animationDelay: '2s'}}></div>
      </div>
      
      {/* Contenu central minimal */}
      <div className={`text-center z-10 transform transition-all duration-700 ${
        isVisible ? 'translate-y-0 opacity-100' : 'translate-y-5 opacity-0'
      }`}>
        {/* Logo avec animation float */}
        <div className="mb-8 flex justify-center">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center animate-float shadow-2xl" style={{
            boxShadow: '0 10px 30px rgba(59, 130, 246, 0.3), 0 0 20px rgba(147, 51, 234, 0.2)'
          }}>
            <svg className="w-10 h-10 text-white animate-pulse" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
            </svg>
          </div>
        </div>
        
        {/* Message principal avec animation avancée */}
        <h1 
          id="welcome-title"
          className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-purple-600 to-blue-800 mb-4 animate-glow-pulse"
          aria-live="polite"
          style={{
            textShadow: '0 0 20px rgba(59, 130, 246, 0.5), 0 0 40px rgba(147, 51, 234, 0.3)',
            filter: 'drop-shadow(0 4px 8px rgba(59, 130, 246, 0.3))'
          }}
        >
          {currentText}
          <span className="animate-advanced-blink text-blue-500 ml-1 font-bold" aria-hidden="true">|</span>
        </h1>
        
        {/* Indicateur de progression avec effet shimmer */}
        <div className="mt-8 w-40 h-2 bg-gray-800 rounded-full mx-auto overflow-hidden shadow-lg">
          <div className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-blue-600 rounded-full animate-shimmer"></div>
        </div>
      </div>
    </div>
  );
};

export default Welcome;