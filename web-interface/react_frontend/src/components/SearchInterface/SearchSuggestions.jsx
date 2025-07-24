/**
 * Composant SearchSuggestions - Suggestions de recherche intelligentes
 */

import React, { useCallback } from 'react';
import PropTypes from 'prop-types';

/**
 * Composant SearchSuggestions
 */
const SearchSuggestions = ({
  suggestions = [],
  onSuggestionSelect,
  maxSuggestions = 5,
  className = ''
}) => {
  // Gestion de la sélection
  const handleSuggestionClick = useCallback((suggestion) => {
    onSuggestionSelect?.(suggestion);
  }, [onSuggestionSelect]);

  // Obtenir l'icône selon le type de suggestion
  const getSuggestionIcon = useCallback((type) => {
    switch (type) {
      case 'recent': return '🕒';
      case 'popular': return '🔥';
      case 'related': return '🔗';
      case 'autocomplete': return '💡';
      default: return '🔍';
    }
  }, []);

  if (suggestions.length === 0) {
    return null;
  }

  const displayedSuggestions = suggestions.slice(0, maxSuggestions);

  return (
    <div className={`search-suggestions ${className}`}>
      <div className="suggestions-header">
        <h4>Suggestions</h4>
      </div>
      
      <div className="suggestions-list">
        {displayedSuggestions.map((suggestion, index) => (
          <button
            key={suggestion.id || index}
            className="suggestion-item"
            onClick={() => handleSuggestionClick(suggestion)}
          >
            <span className="suggestion-icon">
              {getSuggestionIcon(suggestion.type)}
            </span>
            
            <div className="suggestion-content">
              <span className="suggestion-query">
                {suggestion.query}
              </span>
              
              {suggestion.description && (
                <span className="suggestion-description">
                  {suggestion.description}
                </span>
              )}
            </div>
            
            {suggestion.count && (
              <span className="suggestion-count">
                {suggestion.count}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

SearchSuggestions.propTypes = {
  suggestions: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      query: PropTypes.string.isRequired,
      type: PropTypes.string,
      description: PropTypes.string,
      count: PropTypes.number,
      filters: PropTypes.object,
    })
  ),
  onSuggestionSelect: PropTypes.func,
  maxSuggestions: PropTypes.number,
  className: PropTypes.string,
};

export default SearchSuggestions;
