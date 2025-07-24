import React, { createContext, useState, useContext, useEffect } from 'react';

// Définition des thèmes disponibles
const themes = {
  light: {
    name: 'Clair',
    description: 'Thème clair moderne',
    auth: {
      background: 'min-h-screen w-full bg-gradient-to-br from-blue-50 to-white',
      container: 'bg-white rounded-xl shadow-2xl',
      card: 'bg-white rounded-xl shadow-lg border border-gray-100'
    },
    dashboard: {
      background: 'min-h-screen bg-gray-50',
      sidebar: 'bg-white border-r border-gray-200',
      card: 'bg-white rounded-lg shadow-sm border border-gray-200',
      header: 'bg-white border-b border-gray-200',
      content: 'bg-white',
      text: 'text-gray-900',
      textSecondary: 'text-gray-600',
      hover: 'hover:bg-gray-100',
      breadcrumb: 'bg-gray-100/50'
    },
    colors: {
      primary: 'blue-600',
      secondary: 'gray-600', 
      accent: 'blue-500',
      text: 'gray-900',
      textSecondary: 'gray-600'
    }
  },
  
  classic: {
    name: 'Classique',
    description: 'Design classique unifié',
    auth: {
      background: 'min-h-screen w-full bg-gray-200',
      container: 'bg-white rounded-lg shadow-xl',
      card: 'bg-white rounded-lg shadow-md border border-gray-200'
    },
    dashboard: {
      background: 'min-h-screen bg-gray-100',
      sidebar: 'bg-gray-800',
      card: 'bg-white rounded-lg shadow-md border border-gray-200',
      header: 'bg-white border-b border-gray-300',
      content: 'bg-white',
      text: 'text-gray-900',
      textSecondary: 'text-gray-700',
      hover: 'hover:bg-gray-200',
      breadcrumb: 'bg-gray-200/50'
    },
    colors: {
      primary: 'blue-600',
      secondary: 'gray-600',
      accent: 'blue-500',
      text: 'gray-900',
      textSecondary: 'gray-700'
    }
  },

  dark: {
    name: 'Sombre',
    description: 'Thème sombre pour les yeux',
    auth: {
      background: 'min-h-screen w-full bg-gradient-to-br from-gray-900 to-black',
      container: 'bg-gray-800 rounded-xl shadow-2xl border border-gray-700',
      card: 'bg-gray-800 rounded-xl shadow-lg border border-gray-700'
    },
    dashboard: {
      background: 'min-h-screen bg-gray-900',
      sidebar: 'bg-gray-800 border-r border-gray-700',
      card: 'bg-gray-800 rounded-lg shadow-lg border border-gray-700',
      header: 'bg-gray-800 border-b border-gray-700',
      content: 'bg-gray-800',
      text: 'text-white',
      textSecondary: 'text-gray-300',
      hover: 'hover:bg-gray-700',
      breadcrumb: 'bg-gray-800/50'
    },
    colors: {
      primary: 'blue-500',
      secondary: 'purple-500',
      accent: 'indigo-400',
      text: 'white',
      textSecondary: 'gray-300'
    }
  },

};

// Context
const ThemeContext = createContext();

// Provider component
export const ThemeProvider = ({ children }) => {
  const [currentTheme, setCurrentTheme] = useState('dark');
  const [isThemeSelectorOpen, setIsThemeSelectorOpen] = useState(false);

  // Charger le thème depuis le localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('nms_theme');
    if (savedTheme && themes[savedTheme]) {
      setCurrentTheme(savedTheme);
    } else {
      setCurrentTheme('dark');
      localStorage.setItem('nms_theme', 'dark');
    }
  }, []);

  // Sauvegarder le thème lors du changement
  const changeTheme = (themeName) => {
    if (themes[themeName]) {
      setCurrentTheme(themeName);
      localStorage.setItem('nms_theme', themeName);
      console.log(`🎨 Thème changé: ${themes[themeName].name}`);
    }
  };

  // Obtenir le thème actuel
  const getTheme = () => themes[currentTheme];

  // Obtenir des classes CSS pour un composant spécifique
  const getThemeClasses = (component, section = 'auth') => {
    const theme = getTheme();
    if (theme[section] && theme[section][component]) {
      return theme[section][component];
    }
    return '';
  };

  // Obtenir une couleur du thème
  const getThemeColor = (colorName) => {
    const theme = getTheme();
    return theme.colors[colorName] || 'gray-500';
  };

  // Basculer le sélecteur de thème
  const toggleThemeSelector = () => {
    setIsThemeSelectorOpen(!isThemeSelectorOpen);
  };

  const value = {
    currentTheme,
    changeTheme,
    getTheme,
    getThemeClasses,
    getThemeColor,
    themes,
    isThemeSelectorOpen,
    toggleThemeSelector,
    setIsThemeSelectorOpen
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

// Hook personnalisé
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export default ThemeContext;