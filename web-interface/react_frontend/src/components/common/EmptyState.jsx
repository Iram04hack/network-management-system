/**
 * EmptyState - Composant pour afficher un état vide
 * Avec action optionnelle
 */

import React, { memo } from 'react';
import PropTypes from 'prop-types';
import './EmptyState.css';

const EmptyState = ({
  title = 'Aucun élément',
  description = '',
  icon = '📭',
  action = null,
  className = '',
}) => {
  return (
    <div className={`empty-state ${className}`}>
      <div className="empty-state-content">
        <div className="empty-state-icon">{icon}</div>
        <h3 className="empty-state-title">{title}</h3>
        {description && (
          <p className="empty-state-description">{description}</p>
        )}
        {action && (
          <button
            className="empty-state-action"
            onClick={action.onClick}
          >
            {action.label}
          </button>
        )}
      </div>
    </div>
  );
};

EmptyState.propTypes = {
  title: PropTypes.string,
  description: PropTypes.string,
  icon: PropTypes.string,
  action: PropTypes.shape({
    label: PropTypes.string.isRequired,
    onClick: PropTypes.func.isRequired,
  }),
  className: PropTypes.string,
};

export default memo(EmptyState);
