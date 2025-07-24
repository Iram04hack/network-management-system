/**
 * Composant CommandHistory - Historique des commandes exécutées
 */

import React, { useCallback } from 'react';
import PropTypes from 'prop-types';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

/**
 * Composant CommandHistory
 */
const CommandHistory = ({
  history = [],
  onCommandSelect,
  onRepeatCommand,
  maxItems = 20,
  className = ''
}) => {
  // Formatage de la date
  const formatDate = useCallback((dateString) => {
    try {
      return formatDistanceToNow(new Date(dateString), {
        addSuffix: true,
        locale: fr,
      });
    } catch (error) {
      return new Date(dateString).toLocaleDateString();
    }
  }, []);

  // Obtenir l'icône de statut
  const getStatusIcon = useCallback((status) => {
    switch (status) {
      case 'completed': return '✅';
      case 'failed': return '❌';
      case 'pending': return '⏳';
      default: return '📝';
    }
  }, []);

  // Obtenir la couleur de statut
  const getStatusColor = useCallback((status) => {
    switch (status) {
      case 'completed': return '#28a745';
      case 'failed': return '#dc3545';
      case 'pending': return '#ffc107';
      default: return '#6c757d';
    }
  }, []);

  // Gestion de la sélection
  const handleCommandSelect = useCallback((execution) => {
    onCommandSelect?.(execution);
  }, [onCommandSelect]);

  // Gestion de la répétition
  const handleRepeatCommand = useCallback((execution, event) => {
    event.stopPropagation();
    onRepeatCommand?.(execution.id);
  }, [onRepeatCommand]);

  if (history.length === 0) {
    return (
      <div className={`command-history empty ${className}`}>
        <div className="empty-state">
          <div className="empty-icon">📜</div>
          <h4>Aucun historique</h4>
          <p>Les commandes exécutées apparaîtront ici</p>
        </div>
      </div>
    );
  }

  const displayedHistory = history.slice(0, maxItems);

  return (
    <div className={`command-history ${className}`}>
      <div className="history-header">
        <h4>Historique des Commandes</h4>
        <span className="history-count">{history.length}</span>
      </div>
      
      <div className="history-list">
        {displayedHistory.map((execution, index) => (
          <div
            key={execution.id || index}
            className="history-item"
            onClick={() => handleCommandSelect(execution)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleCommandSelect(execution);
              }
            }}
          >
            <div className="history-content">
              <div className="command-info">
                <span 
                  className="status-icon"
                  style={{ color: getStatusColor(execution.status) }}
                >
                  {getStatusIcon(execution.status)}
                </span>
                
                <div className="command-details">
                  <span className="command-name">{execution.name}</span>
                  
                  {execution.parameters && Object.keys(execution.parameters).length > 0 && (
                    <div className="command-parameters">
                      {Object.entries(execution.parameters).map(([key, value]) => (
                        <span key={key} className="parameter">
                          {key}={value}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="execution-meta">
                <span className="execution-date">
                  {formatDate(execution.timestamp || execution.created_at)}
                </span>
                
                {execution.execution_time && (
                  <span className="execution-time">
                    {execution.execution_time}ms
                  </span>
                )}
              </div>
            </div>

            <div className="history-actions">
              {onRepeatCommand && execution.status === 'completed' && (
                <button
                  className="action-button repeat"
                  onClick={(e) => handleRepeatCommand(execution, e)}
                  title="Répéter cette commande"
                >
                  🔄
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

CommandHistory.propTypes = {
  history: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      name: PropTypes.string.isRequired,
      parameters: PropTypes.object,
      status: PropTypes.string.isRequired,
      timestamp: PropTypes.string,
      created_at: PropTypes.string,
      execution_time: PropTypes.number,
    })
  ),
  onCommandSelect: PropTypes.func,
  onRepeatCommand: PropTypes.func,
  maxItems: PropTypes.number,
  className: PropTypes.string,
};

export default CommandHistory;
