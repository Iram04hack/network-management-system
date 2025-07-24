/**
 * Composant CommandSuggestions - Suggestions de commandes disponibles
 */

import React, { useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';

/**
 * Composant CommandSuggestions
 */
const CommandSuggestions = ({
  commands = [],
  onCommandSelect,
  onQuickExecute,
  groupByCategory = true,
  className = ''
}) => {
  // Obtenir l'icône selon la catégorie
  const getCategoryIcon = useCallback((category) => {
    switch (category) {
      case 'network': return '🌐';
      case 'system': return '🖥️';
      case 'analysis': return '📊';
      case 'security': return '🔒';
      case 'monitoring': return '📈';
      default: return '⚡';
    }
  }, []);

  // Obtenir la couleur selon la catégorie
  const getCategoryColor = useCallback((category) => {
    switch (category) {
      case 'network': return '#007bff';
      case 'system': return '#28a745';
      case 'analysis': return '#ffc107';
      case 'security': return '#dc3545';
      case 'monitoring': return '#6f42c1';
      default: return '#6c757d';
    }
  }, []);

  // Grouper les commandes par catégorie
  const groupedCommands = useMemo(() => {
    if (!groupByCategory) {
      return { all: commands };
    }

    return commands.reduce((groups, command) => {
      const category = command.category || 'other';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(command);
      return groups;
    }, {});
  }, [commands, groupByCategory]);

  // Gestion de la sélection
  const handleCommandSelect = useCallback((command) => {
    onCommandSelect?.(command);
  }, [onCommandSelect]);

  // Gestion de l'exécution rapide
  const handleQuickExecute = useCallback((command, event) => {
    event.stopPropagation();
    onQuickExecute?.(command.name, {});
  }, [onQuickExecute]);

  if (commands.length === 0) {
    return (
      <div className={`command-suggestions empty ${className}`}>
        <div className="empty-state">
          <div className="empty-icon">💡</div>
          <h4>Aucune commande</h4>
          <p>Aucune commande disponible</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`command-suggestions ${className}`}>
      <div className="suggestions-header">
        <h4>Commandes Disponibles</h4>
        <span className="commands-count">{commands.length}</span>
      </div>
      
      <div className="suggestions-content">
        {Object.entries(groupedCommands).map(([category, categoryCommands]) => (
          <div key={category} className="command-category">
            {groupByCategory && (
              <div className="category-header">
                <span 
                  className="category-icon"
                  style={{ color: getCategoryColor(category) }}
                >
                  {getCategoryIcon(category)}
                </span>
                <span className="category-name">
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </span>
                <span className="category-count">({categoryCommands.length})</span>
              </div>
            )}

            <div className="commands-list">
              {categoryCommands.map((command, index) => (
                <div
                  key={command.name || index}
                  className="command-item"
                  onClick={() => handleCommandSelect(command)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleCommandSelect(command);
                    }
                  }}
                >
                  <div className="command-content">
                    <div className="command-header">
                      <span className="command-name">{command.name}</span>
                      
                      {!groupByCategory && (
                        <span 
                          className="command-category-badge"
                          style={{ 
                            backgroundColor: getCategoryColor(command.category),
                            color: 'white'
                          }}
                        >
                          {command.category}
                        </span>
                      )}
                    </div>

                    <div className="command-description">
                      {command.description}
                    </div>

                    {command.parameters && command.parameters.length > 0 && (
                      <div className="command-parameters">
                        <span className="parameters-label">Paramètres:</span>
                        <div className="parameters-list">
                          {command.parameters.map((param, paramIndex) => (
                            <span key={paramIndex} className="parameter-tag">
                              {param}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="command-actions">
                    {onQuickExecute && command.parameters && command.parameters.length === 0 && (
                      <button
                        className="action-button execute"
                        onClick={(e) => handleQuickExecute(command, e)}
                        title="Exécuter maintenant"
                      >
                        ▶️
                      </button>
                    )}
                    
                    <button
                      className="action-button select"
                      onClick={() => handleCommandSelect(command)}
                      title="Sélectionner cette commande"
                    >
                      📝
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

CommandSuggestions.propTypes = {
  commands: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      category: PropTypes.string,
      parameters: PropTypes.arrayOf(PropTypes.string),
    })
  ),
  onCommandSelect: PropTypes.func,
  onQuickExecute: PropTypes.func,
  groupByCategory: PropTypes.bool,
  className: PropTypes.string,
};

export default CommandSuggestions;
