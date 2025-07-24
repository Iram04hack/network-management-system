/**
 * ConversationItem - Composant pour afficher un élément de conversation
 * Optimisé pour la virtualisation et les performances
 */

import React, { memo, useCallback } from 'react';
import PropTypes from 'prop-types';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import './ConversationItem.css';

/**
 * Composant ConversationItem mémorisé pour performance
 */
const ConversationItem = ({
  conversation,
  isSelected = false,
  isChecked = false,
  onSelect,
  onDelete,
  onCheck,
  showCheckbox = false,
}) => {
  // Formatage de la date
  const formattedDate = formatDistanceToNow(new Date(conversation.created_at), {
    addSuffix: true,
    locale: fr,
  });

  // Gestion du clic
  const handleClick = useCallback((e) => {
    if (e.target.type === 'checkbox') return; // Éviter le conflit avec la checkbox
    onSelect?.(conversation);
  }, [onSelect, conversation]);

  // Gestion de la checkbox
  const handleCheckboxChange = useCallback((e) => {
    e.stopPropagation();
    onCheck?.(e.target.checked);
  }, [onCheck]);

  // Gestion de la suppression
  const handleDelete = useCallback((e) => {
    e.stopPropagation();
    onDelete?.(conversation.id);
  }, [onDelete, conversation.id]);

  // Calcul du statut
  const hasMessages = conversation.message_count > 0;
  const isRecent = new Date() - new Date(conversation.created_at) < 24 * 60 * 60 * 1000; // 24h

  return (
    <div 
      className={`conversation-item ${isSelected ? 'selected' : ''} ${isRecent ? 'recent' : ''}`}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick(e);
        }
      }}
    >
      {/* Checkbox pour sélection multiple */}
      {showCheckbox && (
        <div className="conversation-checkbox">
          <input
            type="checkbox"
            checked={isChecked}
            onChange={handleCheckboxChange}
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}

      {/* Avatar/Icône */}
      <div className="conversation-avatar">
        <div className={`avatar-circle ${hasMessages ? 'has-messages' : 'empty'}`}>
          {conversation.title.charAt(0).toUpperCase()}
        </div>
        {isRecent && <div className="recent-indicator" />}
      </div>

      {/* Contenu principal */}
      <div className="conversation-content">
        <div className="conversation-header">
          <h3 className="conversation-title" title={conversation.title}>
            {conversation.title}
          </h3>
          <span className="conversation-date">{formattedDate}</span>
        </div>

        <div className="conversation-details">
          {conversation.description && (
            <p className="conversation-description" title={conversation.description}>
              {conversation.description}
            </p>
          )}
          
          <div className="conversation-meta">
            <span className="message-count">
              {conversation.message_count || 0} message{(conversation.message_count || 0) !== 1 ? 's' : ''}
            </span>
            
            {conversation.last_message_at && (
              <span className="last-activity">
                Dernière activité: {formatDistanceToNow(new Date(conversation.last_message_at), {
                  addSuffix: true,
                  locale: fr,
                })}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="conversation-actions">
        {/* Indicateurs de statut */}
        <div className="status-indicators">
          {hasMessages && (
            <div className="status-badge messages" title="Contient des messages">
              💬
            </div>
          )}
          
          {conversation.is_active === false && (
            <div className="status-badge inactive" title="Conversation archivée">
              📁
            </div>
          )}
          
          {conversation.metadata?.priority === 'high' && (
            <div className="status-badge priority" title="Priorité élevée">
              ⭐
            </div>
          )}
        </div>

        {/* Bouton de suppression */}
        <button
          className="delete-button"
          onClick={handleDelete}
          title="Supprimer la conversation"
          aria-label={`Supprimer la conversation ${conversation.title}`}
        >
          🗑️
        </button>
      </div>

      {/* Indicateur de sélection */}
      {isSelected && <div className="selection-indicator" />}
    </div>
  );
};

ConversationItem.propTypes = {
  conversation: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string,
    created_at: PropTypes.string.isRequired,
    last_message_at: PropTypes.string,
    message_count: PropTypes.number,
    is_active: PropTypes.bool,
    metadata: PropTypes.object,
  }).isRequired,
  isSelected: PropTypes.bool,
  isChecked: PropTypes.bool,
  onSelect: PropTypes.func,
  onDelete: PropTypes.func,
  onCheck: PropTypes.func,
  showCheckbox: PropTypes.bool,
};

export default memo(ConversationItem);
