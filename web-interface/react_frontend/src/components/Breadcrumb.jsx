import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const Breadcrumb = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { getThemeClasses } = useTheme();

  // Mapping des routes vers des noms lisibles
  const routeNames = {
    dashboard: 'Tableau de bord',
    monitoring: 'Monitoring',
    equipments: 'Équipements', 
    security: 'Sécurité',
    qos: 'QoS',
    gns3: 'GNS3',
    reports: 'Rapports'
  };

  // Routes qui sont des pages principales (sans parents)
  const mainRoutes = ['dashboard', 'monitoring', 'equipments', 'security', 'qos', 'gns3', 'reports'];

  // Construire le fil d'Ariane à partir de l'URL
  const pathnames = location.pathname.split('/').filter(x => x);
  
  // Afficher seulement si on n'est pas sur la page d'accueil
  if (pathnames.length === 0) return null;
  
  const breadcrumbItems = [
    { name: 'Accueil', path: '/', icon: Home }
  ];

  let currentPath = '';
  pathnames.forEach((name, index) => {
    currentPath += `/${name}`;
    
    if (routeNames[name]) {
      breadcrumbItems.push({
        name: routeNames[name],
        path: currentPath,
        isLast: index === pathnames.length - 1
      });
    }
  });

  if (breadcrumbItems.length <= 1) return null;

  return (
    <nav className={`flex items-center space-x-2 text-sm ${getThemeClasses('textSecondary', 'dashboard')} mb-4 px-6 py-2 ${getThemeClasses('breadcrumb', 'dashboard')} rounded-lg`}>
      {breadcrumbItems.map((item, index) => (
        <div key={item.path} className="flex items-center">
          {index > 0 && (
            <ChevronRight className={`w-4 h-4 mx-2 ${getThemeClasses('textSecondary', 'dashboard')}`} />
          )}
          
          <button
            onClick={() => navigate(item.path)}
            className={`flex items-center space-x-1 transition-colors ${getThemeClasses('hover', 'dashboard')} ${
              item.isLast 
                ? 'text-blue-400 font-medium cursor-default' 
                : `hover:text-blue-400 ${getThemeClasses('textSecondary', 'dashboard')}`
            }`}
            disabled={item.isLast}
          >
            {item.icon && <item.icon className="w-4 h-4" />}
            <span>{item.name}</span>
          </button>
        </div>
      ))}
    </nav>
  );
};

export default Breadcrumb;