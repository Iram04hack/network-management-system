/**
 * Composant DocumentFilters - Filtres pour les documents
 * Filtrage par type, tags, date, taille
 */

import React, { useState, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';

/**
 * Composant DocumentFilters
 */
const DocumentFilters = ({
  onFiltersChange,
  onClearFilters,
  availableTags = [],
  availableTypes = [],
  initialFilters = {},
  className = ''
}) => {
  // État des filtres
  const [filters, setFilters] = useState({
    contentType: '',
    tags: [],
    dateRange: '',
    sizeRange: '',
    searchText: '',
    ...initialFilters
  });

  const [isExpanded, setIsExpanded] = useState(false);

  // Appliquer les filtres
  const applyFilters = useCallback((newFilters) => {
    const updatedFilters = { ...filters, ...newFilters };
    setFilters(updatedFilters);
    onFiltersChange?.(updatedFilters);
  }, [filters, onFiltersChange]);

  // Effacer tous les filtres
  const clearAllFilters = useCallback(() => {
    const emptyFilters = {
      contentType: '',
      tags: [],
      dateRange: '',
      sizeRange: '',
      searchText: '',
    };
    setFilters(emptyFilters);
    onClearFilters?.(emptyFilters);
  }, [onClearFilters]);

  // Gestion du type de contenu
  const handleContentTypeChange = useCallback((contentType) => {
    applyFilters({ contentType });
  }, [applyFilters]);

  // Gestion des tags
  const handleTagToggle = useCallback((tag) => {
    const newTags = filters.tags.includes(tag)
      ? filters.tags.filter(t => t !== tag)
      : [...filters.tags, tag];
    applyFilters({ tags: newTags });
  }, [filters.tags, applyFilters]);

  // Gestion de la plage de dates
  const handleDateRangeChange = useCallback((dateRange) => {
    applyFilters({ dateRange });
  }, [applyFilters]);

  // Gestion de la plage de taille
  const handleSizeRangeChange = useCallback((sizeRange) => {
    applyFilters({ sizeRange });
  }, [applyFilters]);

  // Gestion de la recherche textuelle
  const handleSearchTextChange = useCallback((searchText) => {
    applyFilters({ searchText });
  }, [applyFilters]);

  // Compter les filtres actifs
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (filters.contentType) count++;
    if (filters.tags.length > 0) count++;
    if (filters.dateRange) count++;
    if (filters.sizeRange) count++;
    if (filters.searchText) count++;
    return count;
  }, [filters]);

  // Options de plage de dates
  const dateRangeOptions = [
    { value: '', label: 'Toutes les dates' },
    { value: 'today', label: 'Aujourd\'hui' },
    { value: 'week', label: 'Cette semaine' },
    { value: 'month', label: 'Ce mois' },
    { value: 'year', label: 'Cette année' },
  ];

  // Options de plage de taille
  const sizeRangeOptions = [
    { value: '', label: 'Toutes les tailles' },
    { value: 'small', label: '< 1 MB' },
    { value: 'medium', label: '1-10 MB' },
    { value: 'large', label: '> 10 MB' },
  ];

  return (
    <div className={`document-filters ${isExpanded ? 'expanded' : ''} ${className}`}>
      {/* En-tête des filtres */}
      <div className="filters-header">
        <button
          className="filters-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <span className="toggle-icon">{isExpanded ? '▼' : '▶'}</span>
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
          {/* Recherche textuelle */}
          <div className="filter-group">
            <label className="filter-label">Recherche</label>
            <input
              type="text"
              className="filter-input search-input"
              placeholder="Rechercher dans les titres..."
              value={filters.searchText}
              onChange={(e) => handleSearchTextChange(e.target.value)}
            />
          </div>

          {/* Type de contenu */}
          <div className="filter-group">
            <label className="filter-label">Type de fichier</label>
            <select
              className="filter-select"
              value={filters.contentType}
              onChange={(e) => handleContentTypeChange(e.target.value)}
            >
              <option value="">Tous les types</option>
              {availableTypes.map(type => (
                <option key={type} value={type}>
                  {type.split('/')[1]?.toUpperCase() || type}
                </option>
              ))}
            </select>
          </div>

          {/* Tags */}
          {availableTags.length > 0 && (
            <div className="filter-group">
              <label className="filter-label">Tags</label>
              <div className="tags-filter">
                {availableTags.map(tag => (
                  <button
                    key={tag}
                    className={`tag-filter ${filters.tags.includes(tag) ? 'active' : ''}`}
                    onClick={() => handleTagToggle(tag)}
                  >
                    {tag}
                    {filters.tags.includes(tag) && <span className="tag-remove">✓</span>}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Plage de dates */}
          <div className="filter-group">
            <label className="filter-label">Période</label>
            <select
              className="filter-select"
              value={filters.dateRange}
              onChange={(e) => handleDateRangeChange(e.target.value)}
            >
              {dateRangeOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Plage de taille */}
          <div className="filter-group">
            <label className="filter-label">Taille</label>
            <select
              className="filter-select"
              value={filters.sizeRange}
              onChange={(e) => handleSizeRangeChange(e.target.value)}
            >
              {sizeRangeOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Filtres actifs (affichage compact) */}
      {!isExpanded && activeFiltersCount > 0 && (
        <div className="active-filters-summary">
          {filters.contentType && (
            <span className="active-filter">
              Type: {filters.contentType.split('/')[1]?.toUpperCase()}
              <button onClick={() => handleContentTypeChange('')}>✕</button>
            </span>
          )}
          
          {filters.tags.length > 0 && (
            <span className="active-filter">
              Tags: {filters.tags.length}
              <button onClick={() => applyFilters({ tags: [] })}>✕</button>
            </span>
          )}
          
          {filters.dateRange && (
            <span className="active-filter">
              Date: {dateRangeOptions.find(opt => opt.value === filters.dateRange)?.label}
              <button onClick={() => handleDateRangeChange('')}>✕</button>
            </span>
          )}
          
          {filters.sizeRange && (
            <span className="active-filter">
              Taille: {sizeRangeOptions.find(opt => opt.value === filters.sizeRange)?.label}
              <button onClick={() => handleSizeRangeChange('')}>✕</button>
            </span>
          )}
          
          {filters.searchText && (
            <span className="active-filter">
              Recherche: "{filters.searchText.substring(0, 10)}..."
              <button onClick={() => handleSearchTextChange('')}>✕</button>
            </span>
          )}
        </div>
      )}
    </div>
  );
};

DocumentFilters.propTypes = {
  onFiltersChange: PropTypes.func,
  onClearFilters: PropTypes.func,
  availableTags: PropTypes.arrayOf(PropTypes.string),
  availableTypes: PropTypes.arrayOf(PropTypes.string),
  initialFilters: PropTypes.object,
  className: PropTypes.string,
};

export default DocumentFilters;
