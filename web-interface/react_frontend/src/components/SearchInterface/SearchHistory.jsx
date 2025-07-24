/**
 * Composant SearchHistory - Historique des recherches
 */

import React, { useCallback } from 'react';
import PropTypes from 'prop-types';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

/**
 * Composant SearchHistory
 */
const SearchHistory = ({
  history = [],
  onHistorySelect,
  onHistoryDelete,
  maxHistory = 10,
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

  // Gestion de la sélection
  const handleHistoryClick = useCallback((historyItem) => {
    onHistorySelect?.(historyItem);
  }, [onHistorySelect]);

  // Gestion de la suppression
  const handleHistoryDelete = useCallback((historyItem, event) => {
    event.stopPropagation();
    onHistoryDelete?.(historyItem);
  }, [onHistoryDelete]);

  if (history.length === 0) {
    return null;
  }

  const displayedHistory = history.slice(0, maxHistory);

  return (
    <div className={`search-history ${className}`}>
      <div className="history-header">
        <h4>Historique</h4>
        {onHistoryDelete && (
          <button
            className="clear-history"
            onClick={() => history.forEach(item => onHistoryDelete(item))}
            title="Effacer l'historique"
          >
            🗑️
          </button>
        )}
      </div>
      
      <div className="history-list">
        {displayedHistory.map((historyItem, index) => (
          <div
            key={historyItem.id || index}
            className="history-item"
            onClick={() => handleHistoryClick(historyItem)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleHistoryClick(historyItem);
              }
            }}
          >
            <div className="history-content">
              <span className="history-query">
                {historyItem.query}
              </span>
              
              <div className="history-meta">
                <span className="history-date">
                  {formatDate(historyItem.timestamp || historyItem.created_at)}
                </span>
                
                {historyItem.resultsCount && (
                  <span className="history-results">
                    {historyItem.resultsCount} résultat(s)
                  </span>
                )}
              </div>
              
              {historyItem.filters && Object.keys(historyItem.filters).length > 0 && (
                <div className="history-filters">
                  {Object.entries(historyItem.filters).map(([key, value]) => {
                    if (!value || (Array.isArray(value) && value.length === 0)) return null;
                    return (
                      <span key={key} className="filter-tag">
                        {key}: {Array.isArray(value) ? value.join(', ') : value}
                      </span>
                    );
                  })}
                </div>
              )}
            </div>
            
            {onHistoryDelete && (
              <button
                className="history-delete"
                onClick={(e) => handleHistoryDelete(historyItem, e)}
                title="Supprimer de l'historique"
              >
                ✕
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

SearchHistory.propTypes = {
  history: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      query: PropTypes.string.isRequired,
      timestamp: PropTypes.string,
      created_at: PropTypes.string,
      resultsCount: PropTypes.number,
      filters: PropTypes.object,
    })
  ),
  onHistorySelect: PropTypes.func,
  onHistoryDelete: PropTypes.func,
  maxHistory: PropTypes.number,
  className: PropTypes.string,
};

export default SearchHistory;
