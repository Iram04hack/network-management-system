import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Command, Hash, User, Settings, FileText, Monitor, Shield } from 'lucide-react';

const GlobalSearch = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  // Données de recherche
  const searchData = [
    // Pages principales
    { id: '1', title: 'Tableau de bord', description: 'Vue d\'ensemble du système', type: 'page', icon: Monitor, path: '/dashboard', keywords: ['dashboard', 'accueil', 'home'] },
    { id: '2', title: 'Monitoring', description: 'Surveillance des métriques', type: 'page', icon: Monitor, path: '/monitoring', keywords: ['monitoring', 'métriques', 'surveillance'] },
    { id: '3', title: 'Équipements', description: 'Gestion des équipements réseau', type: 'page', icon: Settings, path: '/equipments', keywords: ['équipements', 'matériel', 'routeur', 'switch'] },
    { id: '4', title: 'Sécurité', description: 'Règles et alertes de sécurité', type: 'page', icon: Shield, path: '/security', keywords: ['sécurité', 'firewall', 'alertes', 'règles'] },
    { id: '5', title: 'QoS', description: 'Qualité de service', type: 'page', icon: Settings, path: '/qos', keywords: ['qos', 'qualité', 'service', 'bande passante'] },
    { id: '6', title: 'GNS3', description: 'Simulation réseau', type: 'page', icon: Settings, path: '/gns3', keywords: ['gns3', 'simulation', 'topologie'] },
    { id: '7', title: 'Rapports', description: 'Génération de rapports', type: 'page', icon: FileText, path: '/reports', keywords: ['rapports', 'export', 'statistiques'] },
    
    // Actions rapides
    { id: '8', title: 'Ajouter équipement', description: 'Ajouter un nouvel équipement', type: 'action', icon: Settings, action: () => navigate('/equipments'), keywords: ['ajouter', 'nouveau', 'équipement'] },
    { id: '9', title: 'Voir alertes', description: 'Consulter les alertes de sécurité', type: 'action', icon: Shield, action: () => navigate('/security'), keywords: ['alertes', 'notifications'] },
    { id: '10', title: 'Paramètres utilisateur', description: 'Gérer votre profil', type: 'action', icon: User, action: () => console.log('Paramètres'), keywords: ['profil', 'paramètres', 'compte'] },
  ];

  // Filtrer les résultats
  const filteredResults = query.length > 0 
    ? searchData.filter(item => 
        item.title.toLowerCase().includes(query.toLowerCase()) ||
        item.description.toLowerCase().includes(query.toLowerCase()) ||
        item.keywords.some(keyword => keyword.toLowerCase().includes(query.toLowerCase()))
      ).slice(0, 8)
    : searchData.slice(0, 8);

  // Gérer les raccourcis clavier
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev < filteredResults.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev > 0 ? prev - 1 : filteredResults.length - 1
          );
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredResults[selectedIndex]) {
            handleSelect(filteredResults[selectedIndex]);
          }
          break;
        case 'Escape':
          onClose();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, filteredResults, onClose]);

  // Focus sur l'input quand le modal s'ouvre
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Gérer la sélection
  const handleSelect = (item) => {
    if (item.path) {
      navigate(item.path);
    } else if (item.action) {
      item.action();
    }
    onClose();
  };

  // Type d'icône selon le type
  const getTypeIcon = (type) => {
    switch (type) {
      case 'page': return Hash;
      case 'action': return Command;
      default: return Search;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-start justify-center pt-20">
      <div className="bg-gray-800 rounded-lg shadow-2xl border border-gray-700 w-full max-w-2xl mx-4">
        {/* Header de recherche */}
        <div className="flex items-center px-4 py-3 border-b border-gray-700">
          <Search className="w-5 h-5 text-gray-400 mr-3" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Rechercher des pages, actions..."
            className="flex-1 bg-transparent text-white placeholder-gray-400 outline-none text-lg"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
          />
          <div className="flex items-center space-x-1 text-xs text-gray-500">
            <kbd className="px-2 py-1 bg-gray-700 rounded">↑</kbd>
            <kbd className="px-2 py-1 bg-gray-700 rounded">↓</kbd>
            <span>pour naviguer</span>
          </div>
        </div>

        {/* Résultats */}
        <div className="max-h-96 overflow-y-auto">
          {filteredResults.length > 0 ? (
            <div className="py-2">
              {filteredResults.map((item, index) => {
                const IconComponent = item.icon;
                const TypeIcon = getTypeIcon(item.type);
                const isSelected = index === selectedIndex;

                return (
                  <div
                    key={item.id}
                    className={`flex items-center px-4 py-3 cursor-pointer transition-colors ${
                      isSelected ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'
                    }`}
                    onClick={() => handleSelect(item)}
                    onMouseEnter={() => setSelectedIndex(index)}
                  >
                    <div className="flex items-center space-x-3 flex-1">
                      <div className={`p-2 rounded-lg ${
                        isSelected ? 'bg-blue-700' : 'bg-gray-700'
                      }`}>
                        <IconComponent className="w-4 h-4" />
                      </div>
                      
                      <div className="flex-1">
                        <div className="font-medium">{item.title}</div>
                        <div className={`text-sm ${
                          isSelected ? 'text-blue-200' : 'text-gray-500'
                        }`}>
                          {item.description}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <TypeIcon className="w-3 h-3 opacity-60" />
                      <span className="text-xs opacity-60">{item.type}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : query.length > 0 ? (
            <div className="py-8 text-center text-gray-500">
              <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>Aucun résultat pour "{query}"</p>
            </div>
          ) : (
            <div className="py-4 px-4">
              <div className="text-xs text-gray-500 font-medium mb-2">PAGES RÉCENTES</div>
              {filteredResults.slice(0, 4).map((item, index) => {
                const IconComponent = item.icon;
                
                return (
                  <div
                    key={item.id}
                    className="flex items-center px-3 py-2 text-gray-400 hover:bg-gray-700 rounded cursor-pointer"
                    onClick={() => handleSelect(item)}
                  >
                    <IconComponent className="w-4 h-4 mr-3" />
                    <span>{item.title}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-gray-700 flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <kbd className="px-2 py-1 bg-gray-700 rounded">Enter</kbd>
              <span>pour sélectionner</span>
            </div>
            <div className="flex items-center space-x-1">
              <kbd className="px-2 py-1 bg-gray-700 rounded">Esc</kbd>
              <span>pour fermer</span>
            </div>
          </div>
          <div className="flex items-center space-x-1">
            <span>Recherche par</span>
            <Command className="w-3 h-3" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default GlobalSearch;