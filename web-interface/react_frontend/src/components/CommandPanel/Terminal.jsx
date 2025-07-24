/**
 * Composant Terminal - Interface terminal avec historique et autocomplétion
 */

import React, { useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import PropTypes from 'prop-types';

/**
 * Composant Terminal
 */
const Terminal = forwardRef(({
  history = [],
  currentInput = '',
  suggestions = [],
  selectedSuggestion = -1,
  loading = false,
  error = null,
  theme = 'dark',
  onInputChange,
  onKeyDown,
  onCommandExecute,
  className = ''
}, ref) => {
  // Références
  const inputRef = useRef(null);
  const historyRef = useRef(null);

  // Exposer les méthodes via ref
  useImperativeHandle(ref, () => ({
    focus: () => inputRef.current?.focus(),
    clear: () => {
      if (inputRef.current) {
        inputRef.current.value = '';
        onInputChange?.('');
      }
    },
    scrollToBottom: () => {
      if (historyRef.current) {
        historyRef.current.scrollTop = historyRef.current.scrollHeight;
      }
    },
  }));

  // Auto-scroll vers le bas quand l'historique change
  useEffect(() => {
    if (historyRef.current) {
      historyRef.current.scrollTop = historyRef.current.scrollHeight;
    }
  }, [history]);

  // Gestion du changement d'input
  const handleInputChange = (e) => {
    onInputChange?.(e.target.value);
  };

  // Gestion des touches
  const handleKeyDown = (e) => {
    onKeyDown?.(e);
  };

  // Formatage de la date
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // Obtenir l'icône de statut
  const getStatusIcon = (status) => {
    switch (status) {
      case 'executing': return '⏳';
      case 'completed': return '✅';
      case 'failed': return '❌';
      default: return '📝';
    }
  };

  // Obtenir la couleur de statut
  const getStatusColor = (status) => {
    switch (status) {
      case 'executing': return '#ffc107';
      case 'completed': return '#28a745';
      case 'failed': return '#dc3545';
      default: return '#6c757d';
    }
  };

  return (
    <div className={`terminal ${theme} ${className}`}>
      {/* Historique des commandes */}
      <div ref={historyRef} className="terminal-history">
        {history.length === 0 && (
          <div className="terminal-welcome">
            <div className="welcome-message">
              <span className="welcome-icon">⚡</span>
              <h4>Terminal de Commandes NMS</h4>
              <p>Tapez une commande ou utilisez les suggestions ci-dessous</p>
            </div>
          </div>
        )}

        {history.map((entry, index) => (
          <div key={entry.id || index} className="terminal-entry">
            {/* Ligne de commande */}
            <div className="command-line">
              <span className="prompt">$</span>
              <span className="command-input">{entry.input}</span>
              <span className="timestamp">{formatTime(entry.timestamp)}</span>
              <span 
                className="status-icon"
                style={{ color: getStatusColor(entry.status) }}
              >
                {getStatusIcon(entry.status)}
              </span>
            </div>

            {/* Sortie de la commande */}
            {entry.result && (
              <div className="command-output">
                {entry.result.output && (
                  <pre className="output-text">{entry.result.output}</pre>
                )}
                
                {entry.result.data && (
                  <div className="output-data">
                    <pre>{JSON.stringify(entry.result.data, null, 2)}</pre>
                  </div>
                )}
                
                {entry.result.execution_time && (
                  <div className="execution-time">
                    Temps d'exécution: {entry.result.execution_time}ms
                  </div>
                )}
              </div>
            )}

            {/* Erreur */}
            {entry.error && (
              <div className="command-error">
                <span className="error-icon">⚠️</span>
                <span className="error-message">{entry.error}</span>
              </div>
            )}

            {/* Indicateur de chargement */}
            {entry.status === 'executing' && (
              <div className="command-loading">
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span>Exécution en cours...</span>
              </div>
            )}
          </div>
        ))}

        {/* Erreur globale */}
        {error && (
          <div className="terminal-error">
            <span className="error-icon">⚠️</span>
            <span className="error-message">{error.message || error}</span>
          </div>
        )}
      </div>

      {/* Ligne de saisie actuelle */}
      <div className="terminal-input-line">
        <span className="prompt">$</span>
        <input
          ref={inputRef}
          type="text"
          value={currentInput}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          className="terminal-input"
          placeholder="Tapez une commande..."
          disabled={loading}
          autoComplete="off"
          spellCheck="false"
        />
        
        {loading && (
          <div className="input-loading">
            <div className="spinner-small"></div>
          </div>
        )}
      </div>

      {/* Suggestions d'autocomplétion */}
      {suggestions.length > 0 && currentInput && (
        <div className="terminal-suggestions">
          {suggestions.map((suggestion, index) => (
            <div
              key={suggestion.name}
              className={`suggestion-item ${index === selectedSuggestion ? 'selected' : ''}`}
            >
              <div className="suggestion-header">
                <span className="suggestion-name">{suggestion.name}</span>
                <span className="suggestion-category">{suggestion.category}</span>
              </div>
              <div className="suggestion-description">
                {suggestion.description}
              </div>
              {suggestion.parameters && suggestion.parameters.length > 0 && (
                <div className="suggestion-parameters">
                  Paramètres: {suggestion.parameters.join(', ')}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
});

Terminal.displayName = 'Terminal';

Terminal.propTypes = {
  history: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      input: PropTypes.string.isRequired,
      timestamp: PropTypes.string.isRequired,
      status: PropTypes.oneOf(['executing', 'completed', 'failed']).isRequired,
      result: PropTypes.object,
      error: PropTypes.string,
    })
  ),
  currentInput: PropTypes.string,
  suggestions: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      category: PropTypes.string,
      parameters: PropTypes.arrayOf(PropTypes.string),
    })
  ),
  selectedSuggestion: PropTypes.number,
  loading: PropTypes.bool,
  error: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  theme: PropTypes.oneOf(['light', 'dark']),
  onInputChange: PropTypes.func,
  onKeyDown: PropTypes.func,
  onCommandExecute: PropTypes.func,
  className: PropTypes.string,
};

export default Terminal;
