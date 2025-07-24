/**
 * Composant MessageComposer - Composition de nouveaux messages
 * Support drag&drop, auto-resize, raccourcis clavier
 * Intégration hook useMessageComposer Phase 3
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useMessageComposer } from '../../hooks';
import './MessageComposer.css';

/**
 * Composant MessageComposer
 */
const MessageComposer = ({
  conversationId,
  onSend,
  disabled = false,
  placeholder = 'Tapez votre message...',
  maxLength = 4000,
  showCharCount = true,
  allowAttachments = true,
  autoFocus = false,
  className = '',
}) => {
  // Hook spécialisé Phase 3
  const {
    currentMessage,
    isComposing,
    canSend,
    updateComposition,
    sendCurrentMessage,
    cancelComposition,
    startComposing,
  } = useMessageComposer(conversationId);

  // État local
  const [isDragOver, setIsDragOver] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [isExpanded, setIsExpanded] = useState(false);

  // Références
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  // Auto-focus
  useEffect(() => {
    if (autoFocus && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [autoFocus]);

  // Auto-resize du textarea
  const adjustTextareaHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.min(textarea.scrollHeight, 200); // Max 200px
      textarea.style.height = `${newHeight}px`;
      
      // Expand/collapse selon la hauteur
      setIsExpanded(newHeight > 60);
    }
  }, []);

  // Gestion du changement de contenu
  const handleContentChange = useCallback((e) => {
    const content = e.target.value;
    
    if (content.length <= maxLength) {
      updateComposition(content);
      adjustTextareaHeight();
    }
  }, [updateComposition, maxLength, adjustTextareaHeight]);

  // Gestion des raccourcis clavier
  const handleKeyDown = useCallback((e) => {
    // Ctrl/Cmd + Enter pour envoyer
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
    
    // Escape pour annuler
    if (e.key === 'Escape') {
      e.preventDefault();
      handleCancel();
    }
    
    // Shift + Enter pour nouvelle ligne (comportement par défaut)
    if (e.shiftKey && e.key === 'Enter') {
      // Laisser le comportement par défaut
      setTimeout(adjustTextareaHeight, 0);
    }
  }, [adjustTextareaHeight]);

  // Envoi du message
  const handleSend = useCallback(async () => {
    if (!canSend || disabled) return;

    try {
      const messageData = {
        content: currentMessage.content.trim(),
        role: 'user',
        metadata: {
          timestamp: new Date().toISOString(),
          attachments: attachments.length > 0 ? attachments : undefined,
        },
      };

      // Utiliser la fonction onSend du parent ou le hook
      if (onSend) {
        await onSend(messageData);
      } else {
        await sendCurrentMessage();
      }

      // Nettoyer après envoi
      setAttachments([]);
      setIsExpanded(false);
      
      // Réinitialiser la hauteur du textarea
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    } catch (error) {
      console.error('Erreur lors de l\'envoi:', error);
    }
  }, [canSend, disabled, currentMessage.content, attachments, onSend, sendCurrentMessage]);

  // Annulation de la composition
  const handleCancel = useCallback(() => {
    cancelComposition();
    setAttachments([]);
    setIsExpanded(false);
    
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [cancelComposition]);

  // Gestion du drag & drop
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);

    if (!allowAttachments) return;

    const files = Array.from(e.dataTransfer.files);
    handleFileSelection(files);
  }, [allowAttachments]);

  // Sélection de fichiers
  const handleFileSelection = useCallback((files) => {
    const validFiles = files.filter(file => {
      // Validation basique des fichiers
      const maxSize = 10 * 1024 * 1024; // 10MB
      const allowedTypes = ['image/', 'text/', 'application/pdf'];
      
      return file.size <= maxSize && 
             allowedTypes.some(type => file.type.startsWith(type));
    });

    const newAttachments = validFiles.map(file => ({
      id: `file_${Date.now()}_${Math.random()}`,
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null,
    }));

    setAttachments(prev => [...prev, ...newAttachments]);
  }, []);

  // Suppression d'une pièce jointe
  const removeAttachment = useCallback((attachmentId) => {
    setAttachments(prev => {
      const updated = prev.filter(att => att.id !== attachmentId);
      // Nettoyer les URLs d'objet
      const removed = prev.find(att => att.id === attachmentId);
      if (removed?.preview) {
        URL.revokeObjectURL(removed.preview);
      }
      return updated;
    });
  }, []);

  // Nettoyage des URLs d'objet
  useEffect(() => {
    return () => {
      attachments.forEach(att => {
        if (att.preview) {
          URL.revokeObjectURL(att.preview);
        }
      });
    };
  }, [attachments]);

  // Calcul du nombre de caractères restants
  const remainingChars = maxLength - currentMessage.content.length;
  const isNearLimit = remainingChars < 100;

  return (
    <div className={`message-composer ${isExpanded ? 'expanded' : ''} ${className}`}>
      {/* Pièces jointes */}
      {attachments.length > 0 && (
        <div className="composer-attachments">
          {attachments.map(attachment => (
            <div key={attachment.id} className="attachment-item">
              {attachment.preview && (
                <img 
                  src={attachment.preview} 
                  alt={attachment.name}
                  className="attachment-preview"
                />
              )}
              <div className="attachment-info">
                <span className="attachment-name">{attachment.name}</span>
                <span className="attachment-size">
                  {(attachment.size / 1024).toFixed(1)} KB
                </span>
              </div>
              <button
                className="remove-attachment"
                onClick={() => removeAttachment(attachment.id)}
                title="Supprimer la pièce jointe"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Zone de composition principale */}
      <div 
        className={`composer-input-area ${isDragOver ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={currentMessage.content}
          onChange={handleContentChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="composer-textarea"
          rows={1}
          maxLength={maxLength}
        />

        {/* Overlay pour drag & drop */}
        {isDragOver && (
          <div className="drag-overlay">
            <div className="drag-message">
              📎 Déposez vos fichiers ici
            </div>
          </div>
        )}
      </div>

      {/* Barre d'outils */}
      <div className="composer-toolbar">
        <div className="toolbar-left">
          {/* Bouton pièces jointes */}
          {allowAttachments && (
            <>
              <button
                className="toolbar-button attach"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
                title="Ajouter une pièce jointe"
              >
                📎
              </button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                style={{ display: 'none' }}
                onChange={(e) => handleFileSelection(Array.from(e.target.files))}
              />
            </>
          )}

          {/* Compteur de caractères */}
          {showCharCount && (
            <span className={`char-count ${isNearLimit ? 'near-limit' : ''}`}>
              {remainingChars}
            </span>
          )}
        </div>

        <div className="toolbar-right">
          {/* Bouton annuler */}
          {isComposing && (
            <button
              className="toolbar-button cancel"
              onClick={handleCancel}
              disabled={disabled}
              title="Annuler (Escape)"
            >
              Annuler
            </button>
          )}

          {/* Bouton envoyer */}
          <button
            className={`toolbar-button send ${canSend ? 'enabled' : 'disabled'}`}
            onClick={handleSend}
            disabled={!canSend || disabled}
            title="Envoyer (Ctrl+Enter)"
          >
            {disabled ? '⏳' : '➤'}
          </button>
        </div>
      </div>

      {/* Aide raccourcis */}
      {isExpanded && (
        <div className="composer-help">
          <span>Ctrl+Enter pour envoyer • Shift+Enter pour nouvelle ligne • Escape pour annuler</span>
        </div>
      )}
    </div>
  );
};

MessageComposer.propTypes = {
  conversationId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  onSend: PropTypes.func,
  disabled: PropTypes.bool,
  placeholder: PropTypes.string,
  maxLength: PropTypes.number,
  showCharCount: PropTypes.bool,
  allowAttachments: PropTypes.bool,
  autoFocus: PropTypes.bool,
  className: PropTypes.string,
};

export default MessageComposer;
