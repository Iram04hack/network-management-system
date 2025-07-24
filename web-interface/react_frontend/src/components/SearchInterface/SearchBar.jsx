/**
 * Composant SearchBar - Barre de recherche avec autocomplétion
 * Support raccourcis clavier et recherche en temps réel
 */

import React, { useState, useCallback, useRef, forwardRef, useImperativeHandle } from 'react';
import PropTypes from 'prop-types';

/**
 * Composant SearchBar
 */
const SearchBar = forwardRef(({
  query = '',
  placeholder = 'Rechercher...',
  loading = false,
  disabled = false,
  showClearButton = true,
  showExpandButton = true,
  isExpanded = false,
  onSearch,
  onQuickSearch,
  onClear,
  onExpand,
  onFocus,
  onBlur,
  className = '',
}, ref) => {
  // État local
  const [isFocused, setIsFocused] = useState(false);
  const [inputValue, setInputValue] = useState(query);

  // Référence interne
  const inputRef = useRef(null);

  // Exposer les méthodes via ref
  useImperativeHandle(ref, () => ({
    focus: () => inputRef.current?.focus(),
    blur: () => inputRef.current?.blur(),
    select: () => inputRef.current?.select(),
    clear: () => {
      setInputValue('');
      onClear?.();
    },
  }));

  // Synchroniser avec la prop query
  React.useEffect(() => {
    setInputValue(query);
  }, [query]);

  // Gestion du changement de valeur
  const handleInputChange = useCallback((e) => {
    const value = e.target.value;
    setInputValue(value);
    
    // Recherche en temps réel (debounced via le parent)
    onQuickSearch?.(value);
  }, [onQuickSearch]);

  // Gestion de la soumission
  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSearch?.(inputValue.trim());
    }
  }, [inputValue, onSearch]);

  // Gestion des raccourcis clavier
  const handleKeyDown = useCallback((e) => {
    switch (e.key) {
      case 'Enter':
        e.preventDefault();
        handleSubmit(e);
        break;
      case 'Escape':
        e.preventDefault();
        if (inputValue) {
          setInputValue('');
          onClear?.();
        } else {
          inputRef.current?.blur();
        }
        break;
      case 'ArrowDown':
        // Permettre la navigation dans les suggestions (géré par le parent)
        break;
      default:
        break;
    }
  }, [inputValue, handleSubmit, onClear]);

  // Gestion du focus
  const handleFocus = useCallback((e) => {
    setIsFocused(true);
    onFocus?.(e);
  }, [onFocus]);

  // Gestion du blur
  const handleBlur = useCallback((e) => {
    setIsFocused(false);
    onBlur?.(e);
  }, [onBlur]);

  // Effacer la recherche
  const handleClear = useCallback(() => {
    setInputValue('');
    onClear?.();
    inputRef.current?.focus();
  }, [onClear]);

  // Basculer l'expansion
  const handleToggleExpand = useCallback(() => {
    onExpand?.();
  }, [onExpand]);

  return (
    <div className={`search-bar ${isFocused ? 'focused' : ''} ${isExpanded ? 'expanded' : ''} ${className}`}>
      <form onSubmit={handleSubmit} className="search-form">
        {/* Icône de recherche */}
        <div className="search-icon">
          {loading ? (
            <div className="search-spinner">
              <div className="spinner"></div>
            </div>
          ) : (
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
          )}
        </div>

        {/* Champ de saisie */}
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled || loading}
          className="search-input"
          autoComplete="off"
          spellCheck="false"
        />

        {/* Bouton effacer */}
        {showClearButton && inputValue && (
          <button
            type="button"
            onClick={handleClear}
            className="search-clear"
            title="Effacer (Escape)"
            disabled={disabled || loading}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}

        {/* Bouton d'expansion */}
        {showExpandButton && (
          <button
            type="button"
            onClick={handleToggleExpand}
            className="search-expand"
            title={isExpanded ? 'Réduire' : 'Étendre la recherche'}
            disabled={disabled || loading}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{
                transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s ease'
              }}
            >
              <polyline points="6,9 12,15 18,9" />
            </svg>
          </button>
        )}

        {/* Bouton de recherche (masqué mais présent pour la soumission) */}
        <button
          type="submit"
          className="search-submit"
          style={{ display: 'none' }}
          disabled={disabled || loading || !inputValue.trim()}
        >
          Rechercher
        </button>
      </form>

      {/* Indicateurs de statut */}
      <div className="search-status">
        {/* Raccourci clavier */}
        {!isFocused && !inputValue && (
          <div className="search-shortcut">
            <kbd>Ctrl</kbd> + <kbd>K</kbd>
          </div>
        )}

        {/* Compteur de caractères */}
        {isFocused && inputValue && (
          <div className="search-char-count">
            {inputValue.length}
          </div>
        )}
      </div>
    </div>
  );
});

SearchBar.displayName = 'SearchBar';

SearchBar.propTypes = {
  query: PropTypes.string,
  placeholder: PropTypes.string,
  loading: PropTypes.bool,
  disabled: PropTypes.bool,
  showClearButton: PropTypes.bool,
  showExpandButton: PropTypes.bool,
  isExpanded: PropTypes.bool,
  onSearch: PropTypes.func,
  onQuickSearch: PropTypes.func,
  onClear: PropTypes.func,
  onExpand: PropTypes.func,
  onFocus: PropTypes.func,
  onBlur: PropTypes.func,
  className: PropTypes.string,
};

export default SearchBar;
