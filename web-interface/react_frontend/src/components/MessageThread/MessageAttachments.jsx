/**
 * Composant MessageAttachments - Affichage des pièces jointes
 * Support images, documents, liens
 */

import React, { memo, useState, useCallback } from 'react';
import PropTypes from 'prop-types';

/**
 * Composant MessageAttachments
 */
const MessageAttachments = ({ attachments = [] }) => {
  const [expandedImage, setExpandedImage] = useState(null);

  // Formatage de la taille de fichier
  const formatFileSize = useCallback((bytes) => {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }, []);

  // Détermination du type d'icône selon le type de fichier
  const getFileIcon = useCallback((mimeType) => {
    if (mimeType.startsWith('image/')) return '🖼️';
    if (mimeType.startsWith('video/')) return '🎥';
    if (mimeType.startsWith('audio/')) return '🎵';
    if (mimeType.includes('pdf')) return '📄';
    if (mimeType.includes('word') || mimeType.includes('document')) return '📝';
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return '📊';
    if (mimeType.includes('powerpoint') || mimeType.includes('presentation')) return '📈';
    if (mimeType.includes('zip') || mimeType.includes('archive')) return '📦';
    if (mimeType.includes('text/')) return '📃';
    return '📎';
  }, []);

  // Gestion du clic sur une image pour l'agrandir
  const handleImageClick = useCallback((attachment) => {
    if (attachment.type?.startsWith('image/')) {
      setExpandedImage(attachment);
    }
  }, []);

  // Fermeture de l'image agrandie
  const closeExpandedImage = useCallback(() => {
    setExpandedImage(null);
  }, []);

  // Téléchargement d'un fichier
  const handleDownload = useCallback((attachment) => {
    if (attachment.url) {
      const link = document.createElement('a');
      link.href = attachment.url;
      link.download = attachment.name || 'fichier';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }, []);

  if (!attachments || attachments.length === 0) {
    return null;
  }

  return (
    <>
      <div className="message-attachments">
        {attachments.map((attachment, index) => {
          const isImage = attachment.type?.startsWith('image/');
          const isVideo = attachment.type?.startsWith('video/');
          const isAudio = attachment.type?.startsWith('audio/');

          return (
            <div key={attachment.id || index} className="attachment-item">
              {/* Prévisualisation pour les images */}
              {isImage && attachment.url && (
                <div 
                  className="attachment-preview image-preview"
                  onClick={() => handleImageClick(attachment)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleImageClick(attachment);
                    }
                  }}
                >
                  <img 
                    src={attachment.url} 
                    alt={attachment.name || 'Image'}
                    loading="lazy"
                  />
                  <div className="preview-overlay">
                    <span className="zoom-icon">🔍</span>
                  </div>
                </div>
              )}

              {/* Prévisualisation pour les vidéos */}
              {isVideo && attachment.url && (
                <div className="attachment-preview video-preview">
                  <video 
                    src={attachment.url}
                    controls
                    preload="metadata"
                    style={{ maxWidth: '300px', maxHeight: '200px' }}
                  >
                    Votre navigateur ne supporte pas la lecture vidéo.
                  </video>
                </div>
              )}

              {/* Prévisualisation pour l'audio */}
              {isAudio && attachment.url && (
                <div className="attachment-preview audio-preview">
                  <audio 
                    src={attachment.url}
                    controls
                    preload="metadata"
                  >
                    Votre navigateur ne supporte pas la lecture audio.
                  </audio>
                </div>
              )}

              {/* Informations du fichier */}
              <div className="attachment-info">
                <div className="attachment-header">
                  <span className="file-icon">
                    {getFileIcon(attachment.type || '')}
                  </span>
                  <span className="file-name" title={attachment.name}>
                    {attachment.name || 'Fichier sans nom'}
                  </span>
                </div>

                <div className="attachment-details">
                  {attachment.size && (
                    <span className="file-size">
                      {formatFileSize(attachment.size)}
                    </span>
                  )}
                  
                  {attachment.type && (
                    <span className="file-type">
                      {attachment.type.split('/')[1]?.toUpperCase() || 'FICHIER'}
                    </span>
                  )}
                </div>

                {/* Actions */}
                <div className="attachment-actions">
                  {attachment.url && (
                    <>
                      <button
                        className="action-button download"
                        onClick={() => handleDownload(attachment)}
                        title="Télécharger"
                      >
                        ⬇️
                      </button>
                      
                      <button
                        className="action-button open"
                        onClick={() => window.open(attachment.url, '_blank')}
                        title="Ouvrir dans un nouvel onglet"
                      >
                        🔗
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal pour l'image agrandie */}
      {expandedImage && (
        <div 
          className="image-modal-overlay"
          onClick={closeExpandedImage}
          role="dialog"
          aria-modal="true"
          aria-label="Image agrandie"
        >
          <div className="image-modal-content">
            <button
              className="close-modal"
              onClick={closeExpandedImage}
              title="Fermer"
              aria-label="Fermer l'image agrandie"
            >
              ✕
            </button>
            
            <img 
              src={expandedImage.url}
              alt={expandedImage.name || 'Image agrandie'}
              className="expanded-image"
            />
            
            <div className="image-modal-info">
              <span className="image-name">{expandedImage.name}</span>
              {expandedImage.size && (
                <span className="image-size">
                  {formatFileSize(expandedImage.size)}
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

MessageAttachments.propTypes = {
  attachments: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      name: PropTypes.string,
      type: PropTypes.string,
      size: PropTypes.number,
      url: PropTypes.string,
    })
  ),
};

export default memo(MessageAttachments);
