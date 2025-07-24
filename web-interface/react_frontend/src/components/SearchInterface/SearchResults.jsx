/**
 * Composant SearchResults - Affichage des résultats de recherche
 * Support modes liste, grille, compact avec actions
 */

import React, { useMemo, useCallback } from 'react';
import PropTypes from 'prop-types';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

/**
 * Composant SearchResults
 */
const SearchResults = ({
  results = [],
  selectedResults = [],
  viewMode = 'list',
  onResultSelect,
  onResultAction,
  showRelevanceScore = true,
  showMetadata = true,
  highlightQuery = '',
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

  // Obtenir l'icône selon le type
  const getTypeIcon = useCallback((type) => {
    switch (type) {
      case 'conversation': return '💬';
      case 'message': return '📝';
      case 'document': return '📄';
      case 'network_analysis': return '🌐';
      case 'user': return '👤';
      case 'equipment': return '🖥️';
      default: return '📎';
    }
  }, []);

  // Obtenir la couleur selon le type
  const getTypeColor = useCallback((type) => {
    switch (type) {
      case 'conversation': return '#007bff';
      case 'message': return '#28a745';
      case 'document': return '#dc3545';
      case 'network_analysis': return '#ffc107';
      case 'user': return '#6f42c1';
      case 'equipment': return '#fd7e14';
      default: return '#6c757d';
    }
  }, []);

  // Surligner le texte de recherche
  const highlightText = useCallback((text, query) => {
    if (!query || !text) return text;
    
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }, []);

  // Gestion de la sélection
  const handleResultClick = useCallback((result) => {
    onResultSelect?.(result);
  }, [onResultSelect]);

  // Gestion des actions
  const handleAction = useCallback((result, action, event) => {
    event.stopPropagation();
    onResultAction?.(result, action);
  }, [onResultAction]);

  // Rendu d'un résultat selon le mode
  const renderResult = useCallback((result, index) => {
    const isSelected = selectedResults.some(r => r.id === result.id);
    const typeIcon = getTypeIcon(result.type);
    const typeColor = getTypeColor(result.type);
    
    const resultClass = `search-result ${viewMode} ${isSelected ? 'selected' : ''}`;

    return (
      <div
        key={result.id || index}
        className={resultClass}
        onClick={() => handleResultClick(result)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleResultClick(result);
          }
        }}
      >
        {/* Mode Liste */}
        {viewMode === 'list' && (
          <>
            <div className="result-header">
              <div className="result-type">
                <span 
                  className="type-icon"
                  style={{ color: typeColor }}
                >
                  {typeIcon}
                </span>
                <span className="type-label">
                  {result.type?.charAt(0).toUpperCase() + result.type?.slice(1)}
                </span>
              </div>
              
              {showRelevanceScore && result.relevance_score && (
                <div className="relevance-score">
                  <div 
                    className="relevance-bar"
                    style={{ width: `${result.relevance_score * 100}%` }}
                  />
                  <span className="relevance-text">
                    {Math.round(result.relevance_score * 100)}%
                  </span>
                </div>
              )}
            </div>

            <div className="result-content">
              <h3 
                className="result-title"
                dangerouslySetInnerHTML={{
                  __html: highlightText(result.title || result.name || 'Sans titre', highlightQuery)
                }}
              />
              
              {result.description && (
                <p 
                  className="result-description"
                  dangerouslySetInnerHTML={{
                    __html: highlightText(result.description, highlightQuery)
                  }}
                />
              )}
              
              {result.content && (
                <p 
                  className="result-excerpt"
                  dangerouslySetInnerHTML={{
                    __html: highlightText(
                      result.content.substring(0, 200) + (result.content.length > 200 ? '...' : ''),
                      highlightQuery
                    )
                  }}
                />
              )}
            </div>

            {showMetadata && (
              <div className="result-metadata">
                <div className="metadata-left">
                  {result.created_at && (
                    <span className="metadata-date">
                      📅 {formatDate(result.created_at)}
                    </span>
                  )}
                  
                  {result.author && (
                    <span className="metadata-author">
                      👤 {result.author.name || result.author.username || 'Anonyme'}
                    </span>
                  )}
                  
                  {result.tags && result.tags.length > 0 && (
                    <div className="metadata-tags">
                      {result.tags.slice(0, 3).map((tag, i) => (
                        <span key={i} className="tag">#{tag}</span>
                      ))}
                      {result.tags.length > 3 && (
                        <span className="tag more">+{result.tags.length - 3}</span>
                      )}
                    </div>
                  )}
                </div>

                <div className="result-actions">
                  <button
                    className="action-button view"
                    onClick={(e) => handleAction(result, 'view', e)}
                    title="Voir"
                  >
                    👁️
                  </button>
                  
                  {result.type === 'document' && (
                    <button
                      className="action-button download"
                      onClick={(e) => handleAction(result, 'download', e)}
                      title="Télécharger"
                    >
                      ⬇️
                    </button>
                  )}
                  
                  <button
                    className="action-button share"
                    onClick={(e) => handleAction(result, 'share', e)}
                    title="Partager"
                  >
                    🔗
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        {/* Mode Grille */}
        {viewMode === 'grid' && (
          <>
            <div className="result-card-header">
              <span 
                className="type-icon large"
                style={{ color: typeColor }}
              >
                {typeIcon}
              </span>
              
              {showRelevanceScore && result.relevance_score && (
                <div className="relevance-badge">
                  {Math.round(result.relevance_score * 100)}%
                </div>
              )}
            </div>

            <div className="result-card-content">
              <h4 
                className="result-title"
                dangerouslySetInnerHTML={{
                  __html: highlightText(result.title || result.name || 'Sans titre', highlightQuery)
                }}
              />
              
              {result.description && (
                <p 
                  className="result-description"
                  dangerouslySetInnerHTML={{
                    __html: highlightText(
                      result.description.substring(0, 100) + (result.description.length > 100 ? '...' : ''),
                      highlightQuery
                    )
                  }}
                />
              )}
            </div>

            <div className="result-card-footer">
              {result.created_at && (
                <span className="card-date">
                  {formatDate(result.created_at)}
                </span>
              )}
              
              <div className="card-actions">
                <button
                  className="action-button small"
                  onClick={(e) => handleAction(result, 'view', e)}
                  title="Voir"
                >
                  👁️
                </button>
              </div>
            </div>
          </>
        )}

        {/* Mode Compact */}
        {viewMode === 'compact' && (
          <>
            <span 
              className="type-icon small"
              style={{ color: typeColor }}
            >
              {typeIcon}
            </span>
            
            <div className="result-compact-content">
              <span 
                className="result-title compact"
                dangerouslySetInnerHTML={{
                  __html: highlightText(result.title || result.name || 'Sans titre', highlightQuery)
                }}
              />
              
              <span className="result-meta compact">
                {result.type} • {result.created_at && formatDate(result.created_at)}
              </span>
            </div>

            {showRelevanceScore && result.relevance_score && (
              <div className="relevance-compact">
                {Math.round(result.relevance_score * 100)}%
              </div>
            )}
          </>
        )}

        {/* Indicateur de sélection */}
        {isSelected && (
          <div className="selection-indicator">
            ✓
          </div>
        )}
      </div>
    );
  }, [viewMode, selectedResults, showRelevanceScore, showMetadata, highlightQuery,
      getTypeIcon, getTypeColor, highlightText, formatDate, handleResultClick, handleAction]);

  // Classes CSS selon le mode
  const containerClass = useMemo(() => {
    const classes = ['search-results', `view-${viewMode}`];
    if (className) classes.push(className);
    return classes.join(' ');
  }, [viewMode, className]);

  if (results.length === 0) {
    return null;
  }

  return (
    <div className={containerClass}>
      {results.map((result, index) => renderResult(result, index))}
    </div>
  );
};

SearchResults.propTypes = {
  results: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      type: PropTypes.string,
      title: PropTypes.string,
      name: PropTypes.string,
      description: PropTypes.string,
      content: PropTypes.string,
      created_at: PropTypes.string,
      relevance_score: PropTypes.number,
      author: PropTypes.object,
      tags: PropTypes.arrayOf(PropTypes.string),
    })
  ),
  selectedResults: PropTypes.array,
  viewMode: PropTypes.oneOf(['list', 'grid', 'compact']),
  onResultSelect: PropTypes.func,
  onResultAction: PropTypes.func,
  showRelevanceScore: PropTypes.bool,
  showMetadata: PropTypes.bool,
  highlightQuery: PropTypes.string,
  className: PropTypes.string,
};

export default SearchResults;
