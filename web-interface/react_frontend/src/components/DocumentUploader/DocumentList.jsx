/**
 * Composant DocumentList - Liste des documents existants
 * Affichage avec tri, filtres et actions
 */

import React, { useMemo, useCallback } from 'react';
import PropTypes from 'prop-types';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import LoadingSpinner from '../common/LoadingSpinner';

/**
 * Composant DocumentList
 */
const DocumentList = ({ 
  documents = [], 
  loading = false, 
  error = null,
  onDocumentSelect,
  onDocumentDelete,
  onDocumentDownload,
  showActions = true,
  showMetadata = true,
  className = '' 
}) => {
  // Formatage de la taille
  const formatFileSize = useCallback((bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }, []);

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

  // Obtenir l'icône selon le type de fichier
  const getFileIcon = useCallback((contentType) => {
    if (!contentType) return '📄';
    
    if (contentType.startsWith('image/')) return '🖼️';
    if (contentType.startsWith('text/')) return '📝';
    if (contentType.includes('pdf')) return '📄';
    if (contentType.includes('json')) return '📋';
    if (contentType.includes('csv')) return '📊';
    if (contentType.includes('word') || contentType.includes('document')) return '📝';
    if (contentType.includes('excel') || contentType.includes('spreadsheet')) return '📊';
    if (contentType.includes('powerpoint') || contentType.includes('presentation')) return '📈';
    
    return '📎';
  }, []);

  // Obtenir la couleur selon le type
  const getTypeColor = useCallback((contentType) => {
    if (!contentType) return '#6c757d';
    
    if (contentType.startsWith('image/')) return '#e91e63';
    if (contentType.startsWith('text/')) return '#2196f3';
    if (contentType.includes('pdf')) return '#f44336';
    if (contentType.includes('json')) return '#ff9800';
    if (contentType.includes('csv')) return '#4caf50';
    if (contentType.includes('word')) return '#2196f3';
    if (contentType.includes('excel')) return '#4caf50';
    if (contentType.includes('powerpoint')) return '#ff5722';
    
    return '#6c757d';
  }, []);

  // Gestion du téléchargement
  const handleDownload = useCallback((document) => {
    if (onDocumentDownload) {
      onDocumentDownload(document);
    } else if (document.url) {
      const link = document.createElement('a');
      link.href = document.url;
      link.download = document.title || document.name || 'document';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }, [onDocumentDownload]);

  // Gestion de la suppression
  const handleDelete = useCallback((document) => {
    if (onDocumentDelete && window.confirm(`Supprimer "${document.title || document.name}" ?`)) {
      onDocumentDelete(document.id);
    }
  }, [onDocumentDelete]);

  // Documents triés par date de création (plus récents en premier)
  const sortedDocuments = useMemo(() => {
    return [...documents].sort((a, b) => 
      new Date(b.created_at || b.uploadedAt || 0) - new Date(a.created_at || a.uploadedAt || 0)
    );
  }, [documents]);

  if (loading && documents.length === 0) {
    return (
      <div className={`document-list loading ${className}`}>
        <LoadingSpinner message="Chargement des documents..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`document-list error ${className}`}>
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <span>Erreur lors du chargement des documents</span>
          <button onClick={() => window.location.reload()}>Réessayer</button>
        </div>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className={`document-list empty ${className}`}>
        <div className="empty-state">
          <div className="empty-icon">📁</div>
          <h3>Aucun document</h3>
          <p>Uploadez votre premier document pour commencer</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`document-list ${className}`}>
      <div className="list-header">
        <h3>Documents ({documents.length})</h3>
        {loading && (
          <div className="loading-indicator">
            <div className="spinner-small"></div>
          </div>
        )}
      </div>

      <div className="documents-grid">
        {sortedDocuments.map((document) => (
          <div 
            key={document.id} 
            className="document-item"
            onClick={() => onDocumentSelect?.(document)}
          >
            {/* En-tête du document */}
            <div className="document-header">
              <div className="document-icon">
                <span 
                  className="file-icon"
                  style={{ color: getTypeColor(document.content_type) }}
                >
                  {getFileIcon(document.content_type)}
                </span>
              </div>
              
              <div className="document-info">
                <h4 className="document-title" title={document.title || document.name}>
                  {document.title || document.name || 'Document sans titre'}
                </h4>
                <div className="document-meta">
                  <span className="document-type">
                    {(document.content_type || 'unknown').split('/')[1]?.toUpperCase() || 'FICHIER'}
                  </span>
                  {document.size && (
                    <span className="document-size">
                      {formatFileSize(document.size)}
                    </span>
                  )}
                  <span className="document-date">
                    {formatDate(document.created_at || document.uploadedAt)}
                  </span>
                </div>
              </div>

              {/* Actions */}
              {showActions && (
                <div className="document-actions">
                  <button
                    className="action-button preview"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDocumentSelect?.(document);
                    }}
                    title="Prévisualiser"
                  >
                    👁️
                  </button>
                  
                  <button
                    className="action-button download"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDownload(document);
                    }}
                    title="Télécharger"
                  >
                    ⬇️
                  </button>
                  
                  {onDocumentDelete && (
                    <button
                      className="action-button delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(document);
                      }}
                      title="Supprimer"
                    >
                      🗑️
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Contenu/Description */}
            {document.description && (
              <div className="document-description">
                <p>{document.description}</p>
              </div>
            )}

            {/* Métadonnées */}
            {showMetadata && (
              <div className="document-metadata">
                {/* Tags */}
                {document.tags && document.tags.length > 0 && (
                  <div className="document-tags">
                    {document.tags.slice(0, 3).map((tag, index) => (
                      <span key={index} className="tag">
                        {tag}
                      </span>
                    ))}
                    {document.tags.length > 3 && (
                      <span className="tag more">+{document.tags.length - 3}</span>
                    )}
                  </div>
                )}

                {/* Statistiques */}
                {document.metadata && (
                  <div className="document-stats">
                    {document.metadata.pages && (
                      <span className="stat">
                        📄 {document.metadata.pages} pages
                      </span>
                    )}
                    {document.metadata.words && (
                      <span className="stat">
                        📝 {document.metadata.words} mots
                      </span>
                    )}
                    {document.metadata.characters && (
                      <span className="stat">
                        🔤 {document.metadata.characters} caractères
                      </span>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Barre de progression si en cours d'upload */}
            {document.status === 'uploading' && document.progress !== undefined && (
              <div className="upload-progress-mini">
                <div className="progress-bar-mini">
                  <div 
                    className="progress-fill-mini"
                    style={{ width: `${document.progress}%` }}
                  />
                </div>
                <span className="progress-text">{Math.round(document.progress)}%</span>
              </div>
            )}

            {/* Indicateur de statut */}
            {document.status && document.status !== 'completed' && (
              <div className={`status-indicator status-${document.status}`}>
                {document.status === 'uploading' && '⏳ Upload...'}
                {document.status === 'processing' && '⚙️ Traitement...'}
                {document.status === 'failed' && '❌ Échec'}
                {document.status === 'pending' && '⏸️ En attente'}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

DocumentList.propTypes = {
  documents: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
      title: PropTypes.string,
      name: PropTypes.string,
      content_type: PropTypes.string,
      size: PropTypes.number,
      created_at: PropTypes.string,
      uploadedAt: PropTypes.string,
      description: PropTypes.string,
      tags: PropTypes.arrayOf(PropTypes.string),
      metadata: PropTypes.object,
      url: PropTypes.string,
      status: PropTypes.string,
      progress: PropTypes.number,
    })
  ),
  loading: PropTypes.bool,
  error: PropTypes.object,
  onDocumentSelect: PropTypes.func,
  onDocumentDelete: PropTypes.func,
  onDocumentDownload: PropTypes.func,
  showActions: PropTypes.bool,
  showMetadata: PropTypes.bool,
  className: PropTypes.string,
};

export default DocumentList;
