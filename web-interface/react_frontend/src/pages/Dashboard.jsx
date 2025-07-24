// Dashboard.jsx - Composant principal avec routing CORRIGÉ
import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { 
  Bell, 
  Home, 
  Shield, 
  Settings,
  FileText,
  Monitor,
  Cpu,
  Router,
  Menu,
  X,
  User,
  Search,
  HelpCircle,
  Globe,
  Server,
  Network,
  Activity
} from 'lucide-react';
import Breadcrumb from '../components/Breadcrumb';
import GlobalSearch from '../components/GlobalSearch';
import HeaderActions from '../components/HeaderActions';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { useTheme } from '../contexts/ThemeContext';

// Dashboard est maintenant un layout qui accepte des children

const Dashboard = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const { getThemeClasses } = useTheme();

  // Raccourcis clavier
  const { shortcuts } = useKeyboardShortcuts(() => setSearchOpen(true));

  // Configuration de la navigation - CHEMINS DIRECTS
  const navigationItems = [
    { id: 'dashboard', path: '/dashboard', icon: Home, label: 'Tableau de bord' },
    { id: 'monitoring', path: '/monitoring', icon: Monitor, label: 'Monitoring' },
    { id: 'network', path: '/network', icon: Network, label: 'Gestion Réseau' },
    { id: 'security', path: '/security', icon: Shield, label: 'Sécurité' },
    { id: 'qos', path: '/qos', icon: Settings, label: 'QoS' },
    { id: 'reports', path: '/reports', icon: FileText, label: 'Rapports' },
    // Modules backend optionnels
    { id: 'api-clients', path: '/api-clients', icon: Server, label: 'API Clients' },
    { id: 'api-views', path: '/api-views', icon: Activity, label: 'API Views' },
    { id: 'api-test', path: '/api-test', icon: Cpu, label: 'Test API Unifié' }
  ];

  // Fonction pour obtenir le titre de la page
  const getPageTitle = () => {
    const currentItem = navigationItems.find(item => 
      location.pathname === item.path
    );
    return currentItem ? currentItem.label : 'Tableau de bord';
  };

  // Fonction pour vérifier si une route est active
  const isActiveRoute = (path) => {
    return location.pathname === path;
  };

  // Gérer la navigation avec loading state
  const handleNavigation = (path) => {
    setIsLoading(true);
    setSidebarOpen(false); // Fermer la sidebar sur mobile
    
    setTimeout(() => {
      navigate(path);
      setIsLoading(false);
    }, 200); // Petit délai pour l'animation
  };

  // Fermer la sidebar quand on clique à l'extérieur (mobile)
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (sidebarOpen && !e.target.closest('.sidebar') && !e.target.closest('.menu-button')) {
        setSidebarOpen(false);
      }
    };
    
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [sidebarOpen]);

  return (
    <div className={`min-h-screen ${getThemeClasses('background', 'dashboard')} ${getThemeClasses('text', 'dashboard')}`}>
      {/* Recherche globale */}
      <GlobalSearch 
        isOpen={searchOpen} 
        onClose={() => setSearchOpen(false)} 
      />

      {/* Header */}
      <header className={`${getThemeClasses('header', 'dashboard')} px-4 md:px-6 py-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Menu hamburger pour mobile */}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className={`md:hidden menu-button p-2 rounded-lg ${getThemeClasses('hover', 'dashboard')} transition-colors`}
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            
            <div>
              <h1 className={`text-xl font-semibold ${getThemeClasses('text', 'dashboard')}`}>
                {getPageTitle()}
              </h1>
              {isLoading && (
                <div className="flex items-center space-x-2 mt-1">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                  <span className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
                    Chargement...
                  </span>
                </div>
              )}
            </div>
          </div>
          
          <HeaderActions 
            onOpenSearch={() => setSearchOpen(true)}
            onShowShortcuts={() => setShowShortcuts(true)}
          />
        </div>
      </header>

      <div className="flex">
        {/* Overlay pour mobile */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <aside className={`
          sidebar fixed md:static inset-y-0 left-0 z-50 md:z-auto
          w-64 md:w-16 ${getThemeClasses('sidebar', 'dashboard')} h-screen
          transform transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}>
          <nav className="p-2 space-y-2 mt-4">
            {navigationItems.map((item) => {
              const IconComponent = item.icon;
              const isActive = isActiveRoute(item.path);
              
              return (
                <div
                  key={item.id}
                  onClick={() => handleNavigation(item.path)}
                  className={`p-3 rounded-lg cursor-pointer transition-all duration-200 group relative flex items-center space-x-3 ${
                    isActive 
                      ? 'bg-blue-600 text-white shadow-lg' 
                      : `${getThemeClasses('hover', 'dashboard')} ${getThemeClasses('textSecondary', 'dashboard')} hover:text-white hover:shadow-md`
                  }`}
                  title={item.label}
                >
                  <IconComponent className="w-5 h-5 flex-shrink-0" />
                  
                  {/* Texte visible sur mobile quand sidebar ouverte */}
                  <span className="md:hidden font-medium">{item.label}</span>
                  
                  {/* Tooltip au survol sur desktop */}
                  <div className="hidden md:block absolute left-16 top-1/2 transform -translate-y-1/2 bg-gray-900 text-white px-2 py-1 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50">
                    {item.label}
                  </div>
                </div>
              );
            })}
          </nav>
        </aside>

        {/* Contenu principal */}
        <div className="flex-1 md:ml-0">
          <div className="p-4 md:p-6">
            <Breadcrumb />
            
            {/* Container avec transitions */}
            <div className={`transition-opacity duration-200 ${isLoading ? 'opacity-50' : 'opacity-100'}`}>
              {children}
            </div>
          </div>
        </div>
      </div>

      {/* Modal d'aide pour les raccourcis */}
      {showShortcuts && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-lg shadow-2xl border border-gray-700 w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h3 className="text-lg font-semibold">Raccourcis clavier</h3>
              <button
                onClick={() => setShowShortcuts(false)}
                className="p-1 rounded hover:bg-gray-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-4 space-y-3">
              {shortcuts.map((shortcut, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-gray-300">{shortcut.description}</span>
                  <kbd className="px-2 py-1 bg-gray-700 rounded text-xs font-mono">
                    {shortcut.key}
                  </kbd>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;