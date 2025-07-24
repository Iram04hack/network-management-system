/**
 * ConversationFilters - Composant pour filtrer et trier les conversations
 * Intégration avec les filtres du hook useConversations
 */

import React, { memo, useCallback } from 'react';
import PropTypes from 'prop-types';
import './ConversationFilters.css';

const ConversationFilters = ({
  filters,
  sorting,
  onFiltersChange,
  onSortingChange,
  onClearFilters,
  className = '',
}) => {
  // Gestion des changements de filtres
  const handleFilterChange = useCallback((key, value) => {
    onFiltersChange?.({
      ...filters,
      [key]: value,
    });
  }, [filters, onFiltersChange]);

  // Gestion du tri
  const handleSortChange = useCallback((field) => {
    const newDirection = sorting.field === field && sorting.direction === 'desc' ? 'asc' : 'desc';
    onSortingChange?.({
      field,
      direction: newDirection,
    });
  }, [sorting, onSortingChange]);

  // Vérifier si des filtres sont actifs
  const hasActiveFilters = filters.search || 
    filters.hasMessages !== null || 
    filters.createdAfter || 
    filters.createdBefore;

  return (
    <div className={`conversation-filters ${className}`}>
      <div className="filters-row">
        {/* Filtre par messages */}
        <div className="filter-group">
          <label htmlFor="message-filter">Messages:</label>
          <select
            id="message-filter"
            value={filters.hasMessages === null ? 'all' : filters.hasMessages.toString()}
            onChange={(e) => {
              const value = e.target.value === 'all' ? null : e.target.value === 'true';
              handleFilterChange('hasMessages', value);
            }}
          >
            <option value="all">Toutes</option>
            <option value="true">Avec messages</option>
            <option value="false">Sans messages</option>
          </select>
        </div>

        {/* Filtre par date de création */}
        <div className="filter-group">
          <label htmlFor="date-after">Créé après:</label>
          <input
            id="date-after"
            type="date"
            value={filters.createdAfter || ''}
            onChange={(e) => handleFilterChange('createdAfter', e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="date-before">Créé avant:</label>
          <input
            id="date-before"
            type="date"
            value={filters.createdBefore || ''}
            onChange={(e) => handleFilterChange('createdBefore', e.target.value)}
          />
        </div>

        {/* Bouton pour effacer les filtres */}
        {hasActiveFilters && (
          <button
            className="clear-filters-button"
            onClick={onClearFilters}
            title="Effacer tous les filtres"
          >
            Effacer filtres
          </button>
        )}
      </div>

      {/* Options de tri */}
      <div className="sorting-row">
        <span className="sorting-label">Trier par:</span>
        
        <button
          className={`sort-button ${sorting.field === 'created_at' ? 'active' : ''}`}
          onClick={() => handleSortChange('created_at')}
        >
          Date de création
          {sorting.field === 'created_at' && (
            <span className="sort-direction">
              {sorting.direction === 'desc' ? ' ↓' : ' ↑'}
            </span>
          )}
        </button>

        <button
          className={`sort-button ${sorting.field === 'title' ? 'active' : ''}`}
          onClick={() => handleSortChange('title')}
        >
          Titre
          {sorting.field === 'title' && (
            <span className="sort-direction">
              {sorting.direction === 'desc' ? ' ↓' : ' ↑'}
            </span>
          )}
        </button>

        <button
          className={`sort-button ${sorting.field === 'message_count' ? 'active' : ''}`}
          onClick={() => handleSortChange('message_count')}
        >
          Nb messages
          {sorting.field === 'message_count' && (
            <span className="sort-direction">
              {sorting.direction === 'desc' ? ' ↓' : ' ↑'}
            </span>
          )}
        </button>

        <button
          className={`sort-button ${sorting.field === 'last_message_at' ? 'active' : ''}`}
          onClick={() => handleSortChange('last_message_at')}
        >
          Dernière activité
          {sorting.field === 'last_message_at' && (
            <span className="sort-direction">
              {sorting.direction === 'desc' ? ' ↓' : ' ↑'}
            </span>
          )}
        </button>
      </div>

      {/* Indicateur de filtres actifs */}
      {hasActiveFilters && (
        <div className="active-filters-indicator">
          <span className="indicator-text">Filtres actifs</span>
          <div className="active-filters-list">
            {filters.search && (
              <span className="active-filter">
                Recherche: "{filters.search}"
              </span>
            )}
            {filters.hasMessages !== null && (
              <span className="active-filter">
                {filters.hasMessages ? 'Avec messages' : 'Sans messages'}
              </span>
            )}
            {filters.createdAfter && (
              <span className="active-filter">
                Après: {new Date(filters.createdAfter).toLocaleDateString()}
              </span>
            )}
            {filters.createdBefore && (
              <span className="active-filter">
                Avant: {new Date(filters.createdBefore).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

ConversationFilters.propTypes = {
  filters: PropTypes.shape({
    search: PropTypes.string,
    hasMessages: PropTypes.bool,
    createdAfter: PropTypes.string,
    createdBefore: PropTypes.string,
  }).isRequired,
  sorting: PropTypes.shape({
    field: PropTypes.string.isRequired,
    direction: PropTypes.oneOf(['asc', 'desc']).isRequired,
  }).isRequired,
  onFiltersChange: PropTypes.func,
  onSortingChange: PropTypes.func,
  onClearFilters: PropTypes.func,
  className: PropTypes.string,
};

export default memo(ConversationFilters);
