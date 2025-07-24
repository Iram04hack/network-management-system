import React from 'react';
import { Sun, Moon, Monitor } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const ThemeToggle = () => {
  const { currentTheme, changeTheme, themes } = useTheme();

  const themeOptions = [
    { key: 'dark', name: 'Sombre', icon: Moon, color: 'text-blue-400' },
    { key: 'modern', name: 'Moderne', icon: Sun, color: 'text-yellow-400' },
    { key: 'classic', name: 'Classique', icon: Monitor, color: 'text-gray-400' },
  ];

  const currentThemeOption = themeOptions.find(theme => theme.key === currentTheme);
  const CurrentIcon = currentThemeOption?.icon || Moon;

  return (
    <div className="relative group">
      <button className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-700 transition-colors">
        <CurrentIcon className={`w-4 h-4 ${currentThemeOption?.color || 'text-gray-400'}`} />
        <span className="text-sm text-gray-300 hidden sm:block">{currentThemeOption?.name}</span>
      </button>

      {/* Dropdown menu */}
      <div className="absolute right-0 top-full mt-2 w-48 bg-gray-800 border border-gray-700 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
        <div className="p-2">
          <div className="text-xs text-gray-500 font-medium mb-2 px-2">THÈME</div>
          {themeOptions.map((theme) => {
            const IconComponent = theme.icon;
            const isActive = currentTheme === theme.key;
            
            return (
              <button
                key={theme.key}
                onClick={() => changeTheme(theme.key)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-left transition-colors ${
                  isActive 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                <IconComponent className={`w-4 h-4 ${isActive ? 'text-white' : theme.color}`} />
                <div className="flex-1">
                  <div className="font-medium">{theme.name}</div>
                  <div className={`text-xs ${isActive ? 'text-blue-200' : 'text-gray-500'}`}>
                    {themes[theme.key]?.description}
                  </div>
                </div>
                {isActive && (
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ThemeToggle;