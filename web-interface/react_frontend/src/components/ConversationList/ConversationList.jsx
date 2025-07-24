/**
 * ConversationList - Composant principal pour afficher la liste des conversations
 * Intégration avec useConversations hook validé Phase 3
 * Virtualisation pour performance, pagination intelligente
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import PropTypes from 'prop-types';
import { FixedSizeList as List } from 'react-window';
import { useConversations, useUI } from '../../hooks';
import ConversationItem from './ConversationItem';
import ConversationFilters from './ConversationFilters';
import ConversationSearch from './ConversationSearch';
import LoadingSpinner from '../common/LoadingSpinner';
import EmptyState from '../common/EmptyState';
import ErrorBoundary from '../common/ErrorBoundary';
import './ConversationList.css';

/**
 * Composant principal ConversationList
 */
const ConversationList = ({
  height = 600,
  itemHeight = 80,
  onConversationSelect,
  selectedConversationId,
  showFilters = true,
  showSearch = true,
  showCheckbox = false, // ✅ Nouvelle prop pour contrôler l'affichage des checkboxes
  className = '',
  ...props
}) => {
  // Filtrer les props qui ne doivent pas être passées au DOM
  const {
    selectedConversation,
    onSwitchToChat,
    compact,
    ...domProps
  } = props;
  // Hooks validés Phase 3
  const {
    conversations,
    currentConversation,
    loading,
    error,
    pagination,
    filters,
    sorting,
    // Actions
    fetchConversations,
    setCurrentConversation,
    createConversation,
    deleteConversation,
    setFilters,
    setSorting,
    clearFilters,
    // Utilitaires
    getFilteredConversations,
    getSortedConversations,
    getStats,
    // Callbacks optimisés
    refresh,
    createAndSelect,
    deleteWithConfirmation,
    quickSearch,
    goToPage,
    nextPage,
    previousPage,
  } = useConversations();

  const { showSuccess, showError, showInfo } = useUI();

  // État local du composant
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [selectedItems, setSelectedItems] = useState(new Set());

  // Données filtrées et triées avec mémorisation
  const processedConversations = useMemo(() => {
    let filtered = conversations;
    
    // Appliquer la recherche locale si présente
    if (searchQuery.trim()) {
      filtered = filtered.filter(conv => 
        conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (conv.description && conv.description.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }
    
    // Appliquer les filtres
    filtered = getFilteredConversations();
    
    // Appliquer le tri
    return getSortedConversations(filtered);
  }, [conversations, searchQuery, getFilteredConversations, getSortedConversations]);

  // Statistiques mémorisées
  const stats = useMemo(() => getStats(), [getStats]);

  // Chargement initial avec logs de diagnostic
  useEffect(() => {
    console.log('🔄 ConversationList useEffect triggered:', {
      conversationsLength: conversations.length,
      loadingFetch: loading.fetch,
      fetchConversationsType: typeof fetchConversations,
      timestamp: new Date().toISOString()
    });

    // DÉSACTIVÉ TEMPORAIREMENT POUR ARRÊTER LA BOUCLE
    // if (conversations.length === 0 && !loading.fetch) {
    //   console.log('📞 ConversationList calling fetchConversations');
    //   fetchConversations();
    // }
  }, [conversations.length, loading.fetch, fetchConversations]);

  // Gestion de la sélection
  const handleConversationSelect = useCallback((conversation) => {
    setCurrentConversation(conversation);
    if (onConversationSelect) {
      onConversationSelect(conversation);
    }
  }, [setCurrentConversation, onConversationSelect]);

  // Création d'une nouvelle conversation
  const handleCreateConversation = useCallback(async () => {
    setIsCreating(true);
    try {
      const newConversation = await createAndSelect({
        title: `Nouvelle conversation ${new Date().toLocaleString()}`,
        description: 'Conversation créée automatiquement',
        metadata: {
          createdFrom: 'ConversationList',
          timestamp: new Date().toISOString(),
        }
      });
      
      if (newConversation.payload) {
        showSuccess('Nouvelle conversation créée avec succès');
        if (onConversationSelect) {
          onConversationSelect(newConversation.payload);
        }
      }
    } catch (error) {
      showError('Erreur lors de la création de la conversation');
      console.error('Erreur création conversation:', error);
    } finally {
      setIsCreating(false);
    }
  }, [createAndSelect, showSuccess, showError, onConversationSelect]);

  // Suppression d'une conversation
  const handleDeleteConversation = useCallback(async (conversationId) => {
    const result = await deleteWithConfirmation(
      conversationId,
      () => window.confirm('Êtes-vous sûr de vouloir supprimer cette conversation ?')
    );
    
    if (result && !result.cancelled) {
      showSuccess('Conversation supprimée avec succès');
      // Rafraîchir la liste
      refresh();
    }
  }, [deleteWithConfirmation, showSuccess, refresh]);

  // Gestion de la recherche
  const handleSearchChange = useCallback((query) => {
    setSearchQuery(query);
    // Recherche globale si la requête est assez longue
    if (query.length >= 3) {
      quickSearch(query);
    }
  }, [quickSearch]);

  // Gestion des filtres
  const handleFiltersChange = useCallback((newFilters) => {
    setFilters(newFilters);
  }, [setFilters]);

  // Gestion du tri
  const handleSortingChange = useCallback((newSorting) => {
    setSorting(newSorting);
  }, [setSorting]);

  // Sélection multiple
  const handleItemSelect = useCallback((conversationId, isSelected) => {
    setSelectedItems(prev => {
      const newSet = new Set(prev);
      if (isSelected) {
        newSet.add(conversationId);
      } else {
        newSet.delete(conversationId);
      }
      return newSet;
    });
  }, []);

  // Actions en lot
  const handleBulkDelete = useCallback(async () => {
    if (selectedItems.size === 0) return;
    
    const confirmed = window.confirm(
      `Êtes-vous sûr de vouloir supprimer ${selectedItems.size} conversation(s) ?`
    );
    
    if (confirmed) {
      const promises = Array.from(selectedItems).map(id => deleteConversation(id));
      try {
        await Promise.all(promises);
        showSuccess(`${selectedItems.size} conversation(s) supprimée(s)`);
        setSelectedItems(new Set());
        refresh();
      } catch (error) {
        showError('Erreur lors de la suppression en lot');
      }
    }
  }, [selectedItems, deleteConversation, showSuccess, showError, refresh]);

  // Rendu d'un élément de la liste virtualisée
  const renderConversationItem = useCallback(({ index, style }) => {
    const conversation = processedConversations[index];
    if (!conversation) return null;

    return (
      <div style={style}>
        <ConversationItem
          conversation={conversation}
          isSelected={conversation.id === selectedConversationId}
          isChecked={selectedItems.has(conversation.id)}
          onSelect={() => handleConversationSelect(conversation)}
          onDelete={() => handleDeleteConversation(conversation.id)}
          onCheck={(isChecked) => handleItemSelect(conversation.id, isChecked)}
          showCheckbox={showCheckbox || selectedItems.size > 0} // ✅ Afficher si prop ou sélection active
        />
      </div>
    );
  }, [
    processedConversations,
    selectedConversationId,
    selectedItems,
    handleConversationSelect,
    handleDeleteConversation,
    handleItemSelect
  ]);

  // Gestion des erreurs
  if (error) {
    return (
      <div className={`conversation-list error ${className}`}>
        <div className="error-message">
          <h3>Erreur de chargement</h3>
          <p>{error.message || 'Une erreur est survenue'}</p>
          <button onClick={refresh} className="retry-button">
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className={`conversation-list ${className}`} {...domProps}>
        {/* En-tête avec statistiques et actions */}
        <div className="conversation-list-header">
          <div className="stats">
            <span className="total-count">{stats.total} conversations</span>
            <span className="with-messages">{stats.withMessages} avec messages</span>
          </div>
          
          <div className="actions">
            {selectedItems.size > 0 && (
              <button 
                onClick={handleBulkDelete}
                className="bulk-delete-button"
                title={`Supprimer ${selectedItems.size} conversation(s)`}
              >
                Supprimer ({selectedItems.size})
              </button>
            )}
            
            <button 
              onClick={handleCreateConversation}
              disabled={isCreating}
              className="create-button primary"
            >
              {isCreating ? 'Création...' : 'Nouvelle conversation'}
            </button>
            
            <button onClick={refresh} className="refresh-button">
              Actualiser
            </button>
          </div>
        </div>

        {/* Recherche */}
        {showSearch && (
          <ConversationSearch
            value={searchQuery}
            onChange={handleSearchChange}
            placeholder="Rechercher dans les conversations..."
            className="conversation-search"
          />
        )}

        {/* Filtres */}
        {showFilters && (
          <ConversationFilters
            filters={filters}
            sorting={sorting}
            onFiltersChange={handleFiltersChange}
            onSortingChange={handleSortingChange}
            onClearFilters={clearFilters}
            className="conversation-filters"
          />
        )}

        {/* Liste des conversations */}
        <div className="conversation-list-content">
          {loading.fetch && conversations.length === 0 ? (
            <LoadingSpinner message="Chargement des conversations..." />
          ) : processedConversations.length === 0 ? (
            <EmptyState
              title="Aucune conversation"
              description={searchQuery ? 
                "Aucune conversation ne correspond à votre recherche" :
                "Créez votre première conversation pour commencer"
              }
              action={!searchQuery ? {
                label: "Créer une conversation",
                onClick: handleCreateConversation
              } : null}
            />
          ) : (
            <List
              height={height}
              itemCount={processedConversations.length}
              itemSize={itemHeight}
              itemData={processedConversations}
              className="conversation-virtual-list"
            >
              {renderConversationItem}
            </List>
          )}
        </div>

        {/* Pagination */}
        {pagination.totalPages > 1 && (
          <div className="conversation-pagination">
            <button 
              onClick={previousPage}
              disabled={!pagination.hasPrevious || loading.fetch}
              className="pagination-button"
            >
              Précédent
            </button>
            
            <span className="pagination-info">
              Page {pagination.currentPage} sur {pagination.totalPages}
            </span>
            
            <button 
              onClick={nextPage}
              disabled={!pagination.hasNext || loading.fetch}
              className="pagination-button"
            >
              Suivant
            </button>
          </div>
        )}

        {/* Indicateur de chargement pour les actions */}
        {(loading.create || loading.update || loading.delete) && (
          <div className="loading-overlay">
            <LoadingSpinner size="small" />
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
};

ConversationList.propTypes = {
  height: PropTypes.number,
  itemHeight: PropTypes.number,
  onConversationSelect: PropTypes.func,
  selectedConversationId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  showFilters: PropTypes.bool,
  showSearch: PropTypes.bool,
  showCheckbox: PropTypes.bool, // ✅ Nouvelle prop ajoutée
  className: PropTypes.string,
};

export default React.memo(ConversationList);
