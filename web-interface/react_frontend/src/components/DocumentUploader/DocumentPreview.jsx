/**
 * Composant DocumentPreview - Prévisualisation de documents
 * Support images, texte, PDF, JSON avec viewer intégré
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';

/**
 * Composant DocumentPreview
 */
const DocumentPreview = ({ file, onClose }) => {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Déterminer le type de prévisualisation
  const previewType = useMemo(() => {
    if (!file) return 'none';
    
    const type = file.type || file.content_type;
    
    if (type.startsWith('image/')) return 'image';
    if (type.startsWith('text/')) return 'text';
    if (type === 'application/json') return 'json';
    if (type === 'application/pdf') return 'pdf';
    if (type.includes('document')) return 'document';
    
    return 'unsupported';
  }, [file]);

  // Charger le contenu du fichier
  const loadFileContent = useCallback(async () => {
    if (!file || previewType === 'image' || previewType === 'pdf') return;

    setLoading(true);
    setError(null);

    try {
      let fileToRead = file.file || file;
      
      // Si c'est un document existant, utiliser l'URL
      if (file.url && !file.file) {
        const response = await fetch(file.url);
        const text = await response.text();
        setContent(text);
      } else if (fileToRead instanceof File) {
        // Lire le fichier local
        const reader = new FileReader();
        
        reader.onload = (e) => {
          let result = e.target.result;
          
          if (previewType === 'json') {
            try {
              result = JSON.stringify(JSON.parse(result), null, 2);
            } catch (jsonError) {
              setError('Fichier JSON invalide');
              return;
            }
          }
          
          setContent(result);
          setLoading(false);
        };
        
        reader.onerror = () => {
          setError('Erreur lors de la lecture du fichier');
          setLoading(false);
        };
        
        reader.readAsText(fileToRead);
      } else if (file.content) {
        // Contenu déjà disponible
        setContent(file.content);
        setLoading(false);
      }
    } catch (err) {
      setError('Erreur lors du chargement: ' + err.message);
      setLoading(false);
    }
  }, [file, previewType]);

  // Charger le contenu au montage
  useEffect(() => {
    loadFileContent();
  }, [loadFileContent]);

  // Gestion des raccourcis clavier
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Formatage de la taille
  const formatFileSize = useCallback((bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }, []);

  // Téléchargement du fichier
  const handleDownload = useCallback(() => {
    if (file.url) {
      const link = document.createElement('a');
      link.href = file.url;
      link.download = file.name || 'document';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else if (file.file) {
      const url = URL.createObjectURL(file.file);
      const link = document.createElement('a');
      link.href = url;
      link.download = file.name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  }, [file]);

  // Copie du contenu
  const handleCopy = useCallback(async () => {
    if (content) {
      try {
        await navigator.clipboard.writeText(content);
        // Feedback visuel (pourrait être une notification)
      } catch (err) {
        console.error('Erreur lors de la copie:', err);
      }
    }
  }, [content]);

  if (!file) return null;

  return (
    <div className="document-preview-overlay" onClick={onClose}>
      <div className="document-preview-modal" onClick={(e) => e.stopPropagation()}>
        {/* En-tête */}
        <div className="preview-header">
          <div className="file-info">
            <h3 className="file-title">{file.name || file.title}</h3>
            <div className="file-meta">
              <span className="file-type">
                {(file.type || file.content_type || 'unknown').split('/')[1]?.toUpperCase()}
              </span>
              {file.size && (
                <span className="file-size">{formatFileSize(file.size)}</span>
              )}
              {file.created_at && (
                <span className="file-date">
                  {new Date(file.created_at).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>

          <div className="preview-actions">
            {content && (
              <button
                className="action-button copy"
                onClick={handleCopy}
                title="Copier le contenu"
              >
                📋
              </button>
            )}
            
            <button
              className="action-button download"
              onClick={handleDownload}
              title="Télécharger"
            >
              ⬇️
            </button>
            
            <button
              className="action-button close"
              onClick={onClose}
              title="Fermer (Escape)"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Contenu de prévisualisation */}
        <div className="preview-content">
          {loading && (
            <div className="preview-loading">
              <div className="loading-spinner"></div>
              <span>Chargement...</span>
            </div>
          )}

          {error && (
            <div className="preview-error">
              <div className="error-icon">⚠️</div>
              <span>{error}</span>
              <button onClick={loadFileContent}>Réessayer</button>
            </div>
          )}

          {!loading && !error && (
            <>
              {/* Image */}
              {previewType === 'image' && (
                <div className="image-preview">
                  <img 
                    src={file.preview || file.url || URL.createObjectURL(file.file)}
                    alt={file.name}
                    className="preview-image"
                  />
                </div>
              )}

              {/* Texte */}
              {previewType === 'text' && (
                <div className="text-preview">
                  <pre className="text-content">{content}</pre>
                </div>
              )}

              {/* JSON */}
              {previewType === 'json' && (
                <div className="json-preview">
                  <pre className="json-content">
                    <code>{content}</code>
                  </pre>
                </div>
              )}

              {/* PDF */}
              {previewType === 'pdf' && (
                <div className="pdf-preview">
                  {file.url ? (
                    <iframe
                      src={file.url}
                      className="pdf-viewer"
                      title={file.name}
                    />
                  ) : (
                    <div className="pdf-placeholder">
                      <div className="pdf-icon">📄</div>
                      <span>Prévisualisation PDF non disponible</span>
                      <button onClick={handleDownload}>Télécharger pour voir</button>
                    </div>
                  )}
                </div>
              )}

              {/* Document Office */}
              {previewType === 'document' && (
                <div className="document-preview">
                  <div className="document-placeholder">
                    <div className="document-icon">📝</div>
                    <span>Prévisualisation de document non disponible</span>
                    <button onClick={handleDownload}>Télécharger pour voir</button>
                  </div>
                </div>
              )}

              {/* Type non supporté */}
              {previewType === 'unsupported' && (
                <div className="unsupported-preview">
                  <div className="unsupported-icon">❓</div>
                  <span>Type de fichier non supporté pour la prévisualisation</span>
                  <button onClick={handleDownload}>Télécharger le fichier</button>
                </div>
              )}
            </>
          )}
        </div>

        {/* Métadonnées */}
        {file.metadata && Object.keys(file.metadata).length > 0 && (
          <div className="preview-metadata">
            <h4>Métadonnées</h4>
            <div className="metadata-grid">
              {Object.entries(file.metadata).map(([key, value]) => (
                <div key={key} className="metadata-item">
                  <span className="metadata-key">{key}:</span>
                  <span className="metadata-value">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tags */}
        {file.tags && file.tags.length > 0 && (
          <div className="preview-tags">
            <h4>Tags</h4>
            <div className="tags-list">
              {file.tags.map((tag, index) => (
                <span key={index} className="tag">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

DocumentPreview.propTypes = {
  file: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    name: PropTypes.string,
    title: PropTypes.string,
    type: PropTypes.string,
    content_type: PropTypes.string,
    size: PropTypes.number,
    url: PropTypes.string,
    preview: PropTypes.string,
    content: PropTypes.string,
    file: PropTypes.object,
    created_at: PropTypes.string,
    metadata: PropTypes.object,
    tags: PropTypes.arrayOf(PropTypes.string),
  }),
  onClose: PropTypes.func.isRequired,
};

export default DocumentPreview;
