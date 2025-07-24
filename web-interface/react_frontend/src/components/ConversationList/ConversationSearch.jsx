/**
 * ConversationSearch - Composant de recherche pour les conversations
 * Avec debounce et suggestions
 */

import React, { memo, useState, useEffect, useCallback, useRef } from 'react';
import PropTypes from 'prop-types';
import './ConversationSearch.css';

const ConversationSearch = ({
  value = '',
  onChange,
  placeholder = 'Rechercher...',
  debounceMs = 300,
  showSuggestions = true,
  className = '',
}) => {
  const [localValue, setLocalValue] = useState(value);
  const [isFocused, setIsFocused] = useState(false);
  const debounceRef = useRef(null);
  const inputRef = useRef(null);

  // Synchroniser avec la valeur externe
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  // Debounce pour la recherche
  const debouncedOnChange = useCallback((searchValue) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    
    debounceRef.current = setTimeout(() => {
      onChange?.(searchValue);
    }, debounceMs);
  }, [onChange, debounceMs]);

  // Gestion du changement de valeur
  const handleInputChange = useCallback((e) => {
    const newValue = e.target.value;
    setLocalValue(newValue);
    debouncedOnChange(newValue);
  }, [debouncedOnChange]);

  // Gestion du focus
  const handleFocus = useCallback(() => {
    setIsFocused(true);
  }, []);

  const handleBlur = useCallback(() => {
    // Délai pour permettre le clic sur les suggestions
    setTimeout(() => setIsFocused(false), 150);
  }, []);

  // Effacer la recherche
  const handleClear = useCallback(() => {
    setLocalValue('');
    onChange?.('');
    inputRef.current?.focus();
  }, [onChange]);

  // Gestion des touches
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') {
      handleClear();
    }
  }, [handleClear]);

  // Nettoyage du debounce
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  // Suggestions simples basées sur des mots-clés courants
  const suggestions = showSuggestions && isFocused && localValue.length >= 2 ? [
    'messages récents',
    'conversations vides',
    'créé aujourd\'hui',
    'créé cette semaine',
    'avec documents',
  ].filter(suggestion => 
    suggestion.toLowerCase().includes(localValue.toLowerCase())
  ) : [];

  return (
    <div className={`conversation-search ${className}`}>
      <div className="search-input-container">
        {/* Icône de recherche */}
        <div className="search-icon">
          🔍
        </div>

        {/* Champ de recherche */}
        <input
          ref={inputRef}
          type="text"
          value={localValue}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="search-input"
          autoComplete="off"
        />

        {/* Bouton d'effacement */}
        {localValue && (
          <button
            className="clear-button"
            onClick={handleClear}
            title="Effacer la recherche"
            type="button"
          >
            ✕
          </button>
        )}
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="search-suggestions">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              className="suggestion-item"
              onClick={() => {
                setLocalValue(suggestion);
                onChange?.(suggestion);
                setIsFocused(false);
              }}
              type="button"
            >
              <span className="suggestion-icon">💡</span>
              <span className="suggestion-text">{suggestion}</span>
            </button>
          ))}
        </div>
      )}

      {/* Indicateur de recherche active */}
      {localValue && (
        <div className="search-status">
          Recherche: "{localValue}"
        </div>
      )}
    </div>
  );
};

ConversationSearch.propTypes = {
  value: PropTypes.string,
  onChange: PropTypes.func,
  placeholder: PropTypes.string,
  debounceMs: PropTypes.number,
  showSuggestions: PropTypes.bool,
  className: PropTypes.string,
};

export default memo(ConversationSearch);
