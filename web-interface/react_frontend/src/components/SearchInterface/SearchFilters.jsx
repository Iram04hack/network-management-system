/**
 * Composant SearchFilters - Filtres visuels avancés pour la recherche
 * Support filtres par type, date, utilisateur, tags
 */

import React, { useState, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';

/**
 * Composant SearchFilters
 */
const SearchFilters = ({
  filters = {},
  onFiltersChange,
  availableTypes = [],
  availableTags = [],
  availableUsers = [],
  showDateFilters = true,
  showTypeFilters = true,
  showTagFilters = true,
  showUserFilters = true,
  className = ''
}) => {
  // État local des filtres
  const [localFilters, setLocalFilters] = useState({
    type: '',
    tags: [],
    userId: '',
    dateRange: '',
    customDateStart: '',
    customDateEnd: '',
    relevanceMin: 0,
    ...filters
  });

  const [isExpanded, setIsExpanded] = useState(false);

  // Appliquer les filtres
  const applyFilters = useCallback((newFilters) => {
    const updatedFilters = { ...localFilters, ...newFilters };
    setLocalFilters(updatedFilters);
    onFiltersChange?.(updatedFilters);
  }, [localFilters, onFiltersChange]);

  // Effacer tous les filtres
  const clearAllFilters = useCallback(() => {
    const emptyFilters = {
      type: '',
      tags: [],
      userId: '',
      dateRange: '',
      customDateStart: '',
      customDateEnd: '',
      relevanceMin: 0,
    };
    setLocalFilters(emptyFilters);
    onFiltersChange?.(emptyFilters);
  }, [onFiltersChange]);

  // Gestion du type
  const handleTypeChange = useCallback((type) => {
    applyFilters({ type });
  }, [applyFilters]);

  // Gestion des tags
  const handleTagToggle = useCallback((tag) => {
    const newTags = localFilters.tags.includes(tag)
      ? localFilters.tags.filter(t => t !== tag)
      : [...localFilters.tags, tag];
    applyFilters({ tags: newTags });
  }, [localFilters.tags, applyFilters]);

  // Gestion de l'utilisateur
  const handleUserChange = useCallback((userId) => {
    applyFilters({ userId });
  }, [applyFilters]);

  // Gestion de la plage de dates
  const handleDateRangeChange = useCallback((dateRange) => {
    applyFilters({ 
      dateRange,
      customDateStart: '',
      customDateEnd: ''
    });
  }, [applyFilters]);

  // Gestion des dates personnalisées
  const handleCustomDateChange = useCallback((field, value) => {
    applyFilters({ 
      [field]: value,
      dateRange: 'custom'
    });
  }, [applyFilters]);

  // Gestion de la pertinence minimale
  const handleRelevanceChange = useCallback((relevanceMin) => {
    applyFilters({ relevanceMin });
  }, [applyFilters]);

  // Compter les filtres actifs
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (localFilters.type) count++;
    if (localFilters.tags.length > 0) count++;
    if (localFilters.userId) count++;
    if (localFilters.dateRange) count++;
    if (localFilters.relevanceMin > 0) count++;
    return count;
  }, [localFilters]);

  // Options de plage de dates
  const dateRangeOptions = [
    { value: '', label: 'Toutes les dates' },
    { value: 'today', label: 'Aujourd\'hui' },
    { value: 'week', label: 'Cette semaine' },
    { value: 'month', label: 'Ce mois' },
    { value: 'quarter', label: 'Ce trimestre' },
    { value: 'year', label: 'Cette année' },
    { value: 'custom', label: 'Période personnalisée' },
  ];

  // Types avec icônes
  const typeOptions = useMemo(() => [
    { value: '', label: 'Tous les types', icon: '🔍' },
    { value: 'conversation', label: 'Conversations', icon: '💬' },
    { value: 'message', label: 'Messages', icon: '📝' },
    { value: 'document', label: 'Documents', icon: '📄' },
    { value: 'network_analysis', label: 'Analyses réseau', icon: '🌐' },
    ...availableTypes.filter(type => 
      !['conversation', 'message', 'document', 'network_analysis'].includes(type)
    ).map(type => ({
      value: type,
      label: type.charAt(0).toUpperCase() + type.slice(1),
      icon: '📎'
    }))
  ], [availableTypes]);

  return (
    <div className={`search-filters ${isExpanded ? 'expanded' : ''} ${className}`}>
      {/* En-tête des filtres */}
      <div className="filters-header">
        <button
          className="filters-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <span className="toggle-icon">
            {isExpanded ? '▼' : '▶'}
          </span>
          <span className="toggle-text">Filtres</span>
          {activeFiltersCount > 0 && (
            <span className="active-count">{activeFiltersCount}</span>
          )}
        </button>

        {activeFiltersCount > 0 && (
          <button
            className="clear-filters"
            onClick={clearAllFilters}
            title="Effacer tous les filtres"
          >
            ✕ Effacer
          </button>
        )}
      </div>

      {/* Contenu des filtres */}
      {isExpanded && (
        <div className="filters-content">
          {/* Filtres par type */}
          {showTypeFilters && (
            <div className="filter-group">
              <label className="filter-label">Type de contenu</label>
              <div className="filter-options type-options">
                {typeOptions.map(option => (
                  <button
                    key={option.value}
                    className={`filter-option ${localFilters.type === option.value ? 'active' : ''}`}
                    onClick={() => handleTypeChange(option.value)}
                  >
                    <span className="option-icon">{option.icon}</span>
                    <span className="option-label">{option.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Filtres par tags */}
          {showTagFilters && availableTags.length > 0 && (
            <div className="filter-group">
              <label className="filter-label">Tags</label>
              <div className="filter-options tag-options">
                {availableTags.map(tag => (
                  <button
                    key={tag}
                    className={`filter-tag ${localFilters.tags.includes(tag) ? 'active' : ''}`}
                    onClick={() => handleTagToggle(tag)}
                  >
                    #{tag}
                    {localFilters.tags.includes(tag) && (
                      <span className="tag-remove">✓</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Filtres par utilisateur */}
          {showUserFilters && availableUsers.length > 0 && (
            <div className="filter-group">
              <label className="filter-label">Utilisateur</label>
              <select
                className="filter-select"
                value={localFilters.userId}
                onChange={(e) => handleUserChange(e.target.value)}
              >
                <option value="">Tous les utilisateurs</option>
                {availableUsers.map(user => (
                  <option key={user.id} value={user.id}>
                    {user.name || user.username || `Utilisateur ${user.id}`}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Filtres par date */}
          {showDateFilters && (
            <div className="filter-group">
              <label className="filter-label">Période</label>
              <select
                className="filter-select"
                value={localFilters.dateRange}
                onChange={(e) => handleDateRangeChange(e.target.value)}
              >
                {dateRangeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>

              {/* Dates personnalisées */}
              {localFilters.dateRange === 'custom' && (
                <div className="custom-date-range">
                  <div className="date-input-group">
                    <label>Du</label>
                    <input
                      type="date"
                      value={localFilters.customDateStart}
                      onChange={(e) => handleCustomDateChange('customDateStart', e.target.value)}
                      className="date-input"
                    />
                  </div>
                  <div className="date-input-group">
                    <label>Au</label>
                    <input
                      type="date"
                      value={localFilters.customDateEnd}
                      onChange={(e) => handleCustomDateChange('customDateEnd', e.target.value)}
                      className="date-input"
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Filtre par pertinence */}
          <div className="filter-group">
            <label className="filter-label">
              Pertinence minimale ({localFilters.relevanceMin}%)
            </label>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={localFilters.relevanceMin}
              onChange={(e) => handleRelevanceChange(parseInt(e.target.value))}
              className="relevance-slider"
            />
            <div className="slider-labels">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>
        </div>
      )}

      {/* Résumé des filtres actifs (mode compact) */}
      {!isExpanded && activeFiltersCount > 0 && (
        <div className="active-filters-summary">
          {localFilters.type && (
            <span className="active-filter">
              Type: {typeOptions.find(opt => opt.value === localFilters.type)?.label}
              <button onClick={() => handleTypeChange('')}>✕</button>
            </span>
          )}
          
          {localFilters.tags.length > 0 && (
            <span className="active-filter">
              Tags: {localFilters.tags.length}
              <button onClick={() => applyFilters({ tags: [] })}>✕</button>
            </span>
          )}
          
          {localFilters.userId && (
            <span className="active-filter">
              Utilisateur: {availableUsers.find(u => u.id === localFilters.userId)?.name || 'Sélectionné'}
              <button onClick={() => handleUserChange('')}>✕</button>
            </span>
          )}
          
          {localFilters.dateRange && (
            <span className="active-filter">
              Date: {dateRangeOptions.find(opt => opt.value === localFilters.dateRange)?.label}
              <button onClick={() => handleDateRangeChange('')}>✕</button>
            </span>
          )}
          
          {localFilters.relevanceMin > 0 && (
            <span className="active-filter">
              Pertinence: ≥{localFilters.relevanceMin}%
              <button onClick={() => handleRelevanceChange(0)}>✕</button>
            </span>
          )}
        </div>
      )}
    </div>
  );
};

SearchFilters.propTypes = {
  filters: PropTypes.object,
  onFiltersChange: PropTypes.func,
  availableTypes: PropTypes.arrayOf(PropTypes.string),
  availableTags: PropTypes.arrayOf(PropTypes.string),
  availableUsers: PropTypes.arrayOf(PropTypes.object),
  showDateFilters: PropTypes.bool,
  showTypeFilters: PropTypes.bool,
  showTagFilters: PropTypes.bool,
  showUserFilters: PropTypes.bool,
  className: PropTypes.string,
};

export default SearchFilters;
