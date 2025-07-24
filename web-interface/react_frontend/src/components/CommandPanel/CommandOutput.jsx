/**
 * Composant CommandOutput - Affichage de la sortie des commandes
 */

import React, { useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';

/**
 * Composant CommandOutput
 */
const CommandOutput = ({
  execution,
  loading = false,
  error = null,
  showMetadata = true,
  className = ''
}) => {
  // Formatage de la date
  const formatDate = useCallback((dateString) => {
    return new Date(dateString).toLocaleString();
  }, []);

  // Formatage du temps d'exécution
  const formatExecutionTime = useCallback((milliseconds) => {
    if (milliseconds < 1000) {
      return `${milliseconds}ms`;
    } else if (milliseconds < 60000) {
      return `${(milliseconds / 1000).toFixed(2)}s`;
    } else {
      const minutes = Math.floor(milliseconds / 60000);
      const seconds = ((milliseconds % 60000) / 1000).toFixed(2);
      return `${minutes}m ${seconds}s`;
    }
  }, []);

  // Obtenir l'icône de statut
  const getStatusIcon = useCallback((status) => {
    switch (status) {
      case 'completed': return '✅';
      case 'failed': return '❌';
      case 'pending': return '⏳';
      case 'running': return '🔄';
      default: return '📝';
    }
  }, []);

  // Obtenir la couleur de statut
  const getStatusColor = useCallback((status) => {
    switch (status) {
      case 'completed': return '#28a745';
      case 'failed': return '#dc3545';
      case 'pending': return '#ffc107';
      case 'running': return '#007bff';
      default: return '#6c757d';
    }
  }, []);

  // Analyser le type de sortie
  const outputType = useMemo(() => {
    if (!execution?.result) return 'none';
    
    const result = execution.result;
    
    if (result.output && typeof result.output === 'string') {
      try {
        JSON.parse(result.output);
        return 'json';
      } catch {
        return 'text';
      }
    }
    
    if (result.data && typeof result.data === 'object') {
      return 'object';
    }
    
    return 'text';
  }, [execution]);

  // Formater la sortie selon le type
  const formatOutput = useCallback((result) => {
    if (!result) return '';
    
    switch (outputType) {
      case 'json':
        try {
          const parsed = JSON.parse(result.output);
          return JSON.stringify(parsed, null, 2);
        } catch {
          return result.output;
        }
      
      case 'object':
        return JSON.stringify(result.data, null, 2);
      
      case 'text':
      default:
        return result.output || JSON.stringify(result, null, 2);
    }
  }, [outputType]);

  if (loading) {
    return (
      <div className={`command-output loading ${className}`}>
        <div className="output-header">
          <h4>Exécution en cours...</h4>
          <div className="loading-indicator">
            <div className="spinner"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`command-output error ${className}`}>
        <div className="output-header">
          <h4>Erreur d'exécution</h4>
          <span className="status-icon error">❌</span>
        </div>
        <div className="output-content">
          <div className="error-message">
            {error.message || error}
          </div>
        </div>
      </div>
    );
  }

  if (!execution) {
    return (
      <div className={`command-output empty ${className}`}>
        <div className="empty-state">
          <div className="empty-icon">📄</div>
          <h4>Aucune sortie</h4>
          <p>Exécutez une commande pour voir sa sortie</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`command-output ${className}`}>
      {/* En-tête de la sortie */}
      <div className="output-header">
        <div className="command-info">
          <h4>{execution.name}</h4>
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

        <div className="execution-status">
          <span 
            className="status-icon"
            style={{ color: getStatusColor(execution.status) }}
          >
            {getStatusIcon(execution.status)}
          </span>
          <span className="status-text">{execution.status}</span>
        </div>
      </div>

      {/* Métadonnées d'exécution */}
      {showMetadata && (
        <div className="output-metadata">
          <div className="metadata-item">
            <span className="metadata-label">Exécuté:</span>
            <span className="metadata-value">
              {formatDate(execution.timestamp || execution.created_at)}
            </span>
          </div>
          
          {execution.execution_time && (
            <div className="metadata-item">
              <span className="metadata-label">Durée:</span>
              <span className="metadata-value">
                {formatExecutionTime(execution.execution_time)}
              </span>
            </div>
          )}
          
          {execution.result?.exit_code !== undefined && (
            <div className="metadata-item">
              <span className="metadata-label">Code de sortie:</span>
              <span className={`metadata-value ${execution.result.exit_code === 0 ? 'success' : 'error'}`}>
                {execution.result.exit_code}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Contenu de la sortie */}
      <div className="output-content">
        {execution.result ? (
          <>
            {/* Sortie principale */}
            {(execution.result.output || execution.result.data) && (
              <div className="output-section">
                <div className="section-header">
                  <h5>Sortie</h5>
                  <span className="output-type">{outputType}</span>
                </div>
                <pre className="output-text">
                  {formatOutput(execution.result)}
                </pre>
              </div>
            )}

            {/* Erreurs */}
            {execution.result.error && (
              <div className="output-section error">
                <div className="section-header">
                  <h5>Erreurs</h5>
                </div>
                <pre className="error-text">
                  {execution.result.error}
                </pre>
              </div>
            )}

            {/* Avertissements */}
            {execution.result.warnings && execution.result.warnings.length > 0 && (
              <div className="output-section warning">
                <div className="section-header">
                  <h5>Avertissements</h5>
                </div>
                <div className="warnings-list">
                  {execution.result.warnings.map((warning, index) => (
                    <div key={index} className="warning-item">
                      <span className="warning-icon">⚠️</span>
                      <span className="warning-text">{warning}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Statistiques */}
            {execution.result.stats && (
              <div className="output-section stats">
                <div className="section-header">
                  <h5>Statistiques</h5>
                </div>
                <div className="stats-grid">
                  {Object.entries(execution.result.stats).map(([key, value]) => (
                    <div key={key} className="stat-item">
                      <span className="stat-label">{key}:</span>
                      <span className="stat-value">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="no-output">
            <span className="no-output-icon">📭</span>
            <span>Aucune sortie générée</span>
          </div>
        )}
      </div>

      {/* Actions sur la sortie */}
      <div className="output-actions">
        <button
          className="action-button copy"
          onClick={() => {
            if (execution.result) {
              navigator.clipboard.writeText(formatOutput(execution.result));
            }
          }}
          title="Copier la sortie"
        >
          📋 Copier
        </button>
        
        <button
          className="action-button download"
          onClick={() => {
            if (execution.result) {
              const blob = new Blob([formatOutput(execution.result)], { type: 'text/plain' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `${execution.name}_output.txt`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              URL.revokeObjectURL(url);
            }
          }}
          title="Télécharger la sortie"
        >
          ⬇️ Télécharger
        </button>
      </div>
    </div>
  );
};

CommandOutput.propTypes = {
  execution: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    name: PropTypes.string.isRequired,
    parameters: PropTypes.object,
    status: PropTypes.string.isRequired,
    timestamp: PropTypes.string,
    created_at: PropTypes.string,
    execution_time: PropTypes.number,
    result: PropTypes.object,
  }),
  loading: PropTypes.bool,
  error: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  showMetadata: PropTypes.bool,
  className: PropTypes.string,
};

export default CommandOutput;
