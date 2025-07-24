import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Bell, 
  User, 
  Settings, 
  HelpCircle, 
  Moon, 
  Sun, 
  Monitor,
  ChevronDown,
  LogOut
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import sessionService from '../services/sessionService';

const HeaderActions = ({ onOpenSearch, onShowShortcuts }) => {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [userInfo, setUserInfo] = useState({ displayName: 'Utilisateur', email: 'user@system.local', role: 'Utilisateur' });
  const { currentTheme, changeTheme, themes, getThemeClasses } = useTheme();

  // Charger les informations utilisateur
  useEffect(() => {
    const sessionData = sessionService.getSessionData();
    if (sessionData?.user) {
      const displayName = sessionService.getDisplayName(sessionData.user);
      const orgInfo = sessionService.getOrganizationInfo(sessionData.user);
      const email = sessionData.user.email || 'user@system.local';
      
      setUserInfo({
        displayName,
        email,
        role: orgInfo.role
      });
    }
  }, []);

  const themeOptions = [
    { key: 'dark', name: 'Sombre', icon: Moon },
    { key: 'light', name: 'Clair', icon: Sun },
    { key: 'classic', name: 'Classique', icon: Monitor },
  ];

  const currentThemeOption = themeOptions.find(theme => theme.key === currentTheme);

  return (
    <div className="flex items-center space-x-2">
      {/* Bouton de recherche */}
      <button
        onClick={onOpenSearch}
        className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${getThemeClasses('hover', 'dashboard')} transition-colors group`}
        title="Rechercher (Ctrl+K)"
      >
        <Search className={`w-4 h-4 ${getThemeClasses('textSecondary', 'dashboard')} group-hover:${getThemeClasses('text', 'dashboard')}`} />
        <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')} hidden lg:block`}>Rechercher...</span>
        <kbd className={`hidden lg:block px-2 py-1 text-xs ${getThemeClasses('card', 'dashboard')} rounded`}>⌘K</kbd>
      </button>

      {/* Notifications */}
      <button className={`p-2 rounded-lg ${getThemeClasses('hover', 'dashboard')} transition-colors relative`}>
        <Bell className={`w-5 h-5 ${getThemeClasses('textSecondary', 'dashboard')} hover:${getThemeClasses('text', 'dashboard')}`} />
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></div>
      </button>

      {/* Menu utilisateur avec toutes les actions */}
      <div className="relative">
        <button
          onClick={() => setShowUserMenu(!showUserMenu)}
          className={`flex items-center space-x-2 p-2 rounded-lg ${getThemeClasses('hover', 'dashboard')} transition-colors`}
        >
          <div className={`w-8 h-8 ${getThemeClasses('card', 'dashboard')} rounded-full flex items-center justify-center`}>
            <User className="w-4 h-4" />
          </div>
          <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')} hidden sm:block`}>{userInfo.displayName}</span>
          <ChevronDown className={`w-4 h-4 ${getThemeClasses('textSecondary', 'dashboard')}`} />
        </button>

        {/* Menu déroulant */}
        {showUserMenu && (
          <div className={`absolute right-0 top-full mt-2 w-64 ${getThemeClasses('card', 'dashboard')} rounded-lg shadow-xl z-50`}>
            {/* Section utilisateur */}
            <div className={`p-4 border-b border-gray-300 ${currentTheme === 'dark' ? 'border-gray-700' : ''}`}>
              <div className="flex items-center space-x-3">
                <div className={`w-10 h-10 ${getThemeClasses('sidebar', 'dashboard')} rounded-full flex items-center justify-center`}>
                  <User className="w-5 h-5" />
                </div>
                <div>
                  <div className={`font-medium ${getThemeClasses('text', 'dashboard')}`}>{userInfo.displayName}</div>
                  <div className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>{userInfo.email}</div>
                </div>
              </div>
            </div>

            {/* Section thème */}
            <div className="p-2">
              <div className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')} font-medium mb-2 px-2`}>THÈME</div>
              {themeOptions.map((theme) => {
                const IconComponent = theme.icon;
                const isActive = currentTheme === theme.key;
                
                return (
                  <button
                    key={theme.key}
                    onClick={() => {
                      changeTheme(theme.key);
                      setShowUserMenu(false);
                    }}
                    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-left transition-colors ${
                      isActive 
                        ? 'bg-blue-600 text-white' 
                        : `${getThemeClasses('textSecondary', 'dashboard')} ${getThemeClasses('hover', 'dashboard')} hover:${getThemeClasses('text', 'dashboard')}`
                    }`}
                  >
                    <IconComponent className="w-4 h-4" />
                    <span className="flex-1">{theme.name}</span>
                    {isActive && (
                      <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                    )}
                  </button>
                );
              })}
            </div>

            <div className={`border-t ${currentTheme === 'dark' ? 'border-gray-700' : 'border-gray-300'} p-2`}>
              {/* Actions utilisateur */}
              <button
                onClick={() => {
                  onShowShortcuts();
                  setShowUserMenu(false);
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md ${getThemeClasses('textSecondary', 'dashboard')} ${getThemeClasses('hover', 'dashboard')} hover:${getThemeClasses('text', 'dashboard')} transition-colors`}
              >
                <HelpCircle className="w-4 h-4" />
                <span>Raccourcis clavier</span>
              </button>

              <button className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md ${getThemeClasses('textSecondary', 'dashboard')} ${getThemeClasses('hover', 'dashboard')} hover:${getThemeClasses('text', 'dashboard')} transition-colors`}>
                <Settings className="w-4 h-4" />
                <span>Paramètres</span>
              </button>

              <div className={`border-t ${currentTheme === 'dark' ? 'border-gray-700' : 'border-gray-300'} my-2`}></div>

              <button className="w-full flex items-center space-x-3 px-3 py-2 rounded-md text-red-400 hover:bg-red-900/20 hover:text-red-300 transition-colors">
                <LogOut className="w-4 h-4" />
                <span>Déconnexion</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Overlay pour fermer le menu */}
      {showUserMenu && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowUserMenu(false)}
        />
      )}
    </div>
  );
};

export default HeaderActions;