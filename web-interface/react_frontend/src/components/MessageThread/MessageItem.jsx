/**
 * Composant MessageItem - Affichage d'un message individuel
 * Support des différents rôles (user, assistant, system)
 * Gestion des états (sending, failed, delivered)
 */

import React, { memo, useMemo } from 'react';
import PropTypes from 'prop-types';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import MessageAttachments from './MessageAttachments';
import './MessageItem.css';

/**
 * Composant MessageItem
 */
const MessageItem = ({
  message,
  isSelected = false,
  showTimestamp = true,
  showAvatar = true,
  onSelect,
  onRetry,
  onCopy,
  onDelete,
}) => {
  // Formatage de la date
  const formattedDate = useMemo(() => {
    if (!message.created_at) return '';
    
    try {
      return formatDistanceToNow(new Date(message.created_at), {
        addSuffix: true,
        locale: fr,
      });
    } catch (error) {
      return new Date(message.created_at).toLocaleString();
    }
  }, [message.created_at]);

  // Détermination du style selon le rôle
  const messageClass = useMemo(() => {
    const classes = ['message-item', `role-${message.role}`];
    
    if (isSelected) classes.push('selected');
    if (message.status) classes.push(`status-${message.status}`);
    if (message.metadata?.priority) classes.push(`priority-${message.metadata.priority}`);
    
    return classes.join(' ');
  }, [message.role, message.status, message.metadata?.priority, isSelected]);

  // Avatar selon le rôle
  const getAvatar = useMemo(() => {
    switch (message.role) {
      case 'user':
        return {
          icon: '👤',
          label: 'Utilisateur',
          color: '#007bff'
        };
      case 'assistant':
        return {
          icon: '🤖',
          label: 'Assistant IA',
          color: '#28a745'
        };
      case 'system':
        return {
          icon: '⚙️',
          label: 'Système',
          color: '#6c757d'
        };
      default:
        return {
          icon: '💬',
          label: 'Message',
          color: '#6c757d'
        };
    }
  }, [message.role]);

  // Indicateur de statut
  const getStatusIndicator = useMemo(() => {
    switch (message.status) {
      case 'sending':
        return { icon: '⏳', label: 'Envoi en cours...', color: '#ffc107' };
      case 'failed':
        return { icon: '❌', label: 'Échec d\'envoi', color: '#dc3545' };
      case 'delivered':
        return { icon: '✓', label: 'Livré', color: '#28a745' };
      case 'read':
        return { icon: '✓✓', label: 'Lu', color: '#007bff' };
      default:
        return null;
    }
  }, [message.status]);

  // Gestion du clic
  const handleClick = () => {
    onSelect?.(message);
  };

  // Copie du contenu
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      onCopy?.(message);
    } catch (error) {
      console.error('Erreur lors de la copie:', error);
    }
  };

  // Formatage du contenu (support basique Markdown)
  const formatContent = (content) => {
    if (!content) return '';
    
    // Remplacements basiques pour le markdown
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  };

  return (
    <div 
      className={messageClass}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      {/* Avatar */}
      {showAvatar && (
        <div className="message-avatar">
          <div 
            className="avatar-circle"
            style={{ backgroundColor: getAvatar.color }}
            title={getAvatar.label}
          >
            {getAvatar.icon}
          </div>
        </div>
      )}

      {/* Contenu principal */}
      <div className="message-content">
        {/* En-tête du message */}
        <div className="message-header">
          <span className="message-role">{getAvatar.label}</span>
          
          {showTimestamp && (
            <span className="message-timestamp" title={new Date(message.created_at).toLocaleString()}>
              {formattedDate}
            </span>
          )}
          
          {/* Indicateur de statut */}
          {getStatusIndicator && (
            <span 
              className="message-status"
              style={{ color: getStatusIndicator.color }}
              title={getStatusIndicator.label}
            >
              {getStatusIndicator.icon}
            </span>
          )}
        </div>

        {/* Corps du message */}
        <div className="message-body">
          <div 
            className="message-text"
            dangerouslySetInnerHTML={{ __html: formatContent(message.content) }}
          />
          
          {/* Pièces jointes */}
          {message.attachments && message.attachments.length > 0 && (
            <MessageAttachments attachments={message.attachments} />
          )}
          
          {/* Métadonnées */}
          {message.metadata && Object.keys(message.metadata).length > 0 && (
            <div className="message-metadata">
              {message.metadata.tokens && (
                <span className="token-count" title="Nombre de tokens">
                  🔢 {message.metadata.tokens}
                </span>
              )}
              
              {message.metadata.model && (
                <span className="model-info" title="Modèle utilisé">
                  🧠 {message.metadata.model}
                </span>
              )}
              
              {message.metadata.responseTime && (
                <span className="response-time" title="Temps de réponse">
                  ⏱️ {message.metadata.responseTime}ms
                </span>
              )}
            </div>
          )}
        </div>

        {/* Actions du message */}
        <div className="message-actions">
          {/* Bouton copier */}
          <button
            className="action-button copy"
            onClick={(e) => {
              e.stopPropagation();
              handleCopy();
            }}
            title="Copier le message"
          >
            📋
          </button>

          {/* Bouton retry pour les messages échoués */}
          {message.status === 'failed' && onRetry && (
            <button
              className="action-button retry"
              onClick={(e) => {
                e.stopPropagation();
                onRetry(message);
              }}
              title="Réessayer l'envoi"
            >
              🔄
            </button>
          )}

          {/* Bouton supprimer */}
          {onDelete && (
            <button
              className="action-button delete"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(message);
              }}
              title="Supprimer le message"
            >
              🗑️
            </button>
          )}

          {/* Indicateur de sélection */}
          {isSelected && (
            <div className="selection-indicator">
              ✓
            </div>
          )}
        </div>
      </div>

      {/* Barre de progression pour les messages en cours d'envoi */}
      {message.status === 'sending' && (
        <div className="sending-progress">
          <div className="progress-bar">
            <div className="progress-fill"></div>
          </div>
        </div>
      )}
    </div>
  );
};

MessageItem.propTypes = {
  message: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    role: PropTypes.oneOf(['user', 'assistant', 'system']).isRequired,
    content: PropTypes.string.isRequired,
    created_at: PropTypes.string.isRequired,
    status: PropTypes.oneOf(['sending', 'delivered', 'failed', 'read']),
    metadata: PropTypes.object,
    attachments: PropTypes.array,
  }).isRequired,
  isSelected: PropTypes.bool,
  showTimestamp: PropTypes.bool,
  showAvatar: PropTypes.bool,
  onSelect: PropTypes.func,
  onRetry: PropTypes.func,
  onCopy: PropTypes.func,
  onDelete: PropTypes.func,
};

export default memo(MessageItem);
