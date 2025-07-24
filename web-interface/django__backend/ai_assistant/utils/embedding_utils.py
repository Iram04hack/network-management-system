"""
Utilitaires pour la génération et la manipulation des embeddings vectoriels.

Ce module fournit des fonctions utilitaires pour générer et manipuler des embeddings vectoriels
utilisés dans la recherche sémantique de la base de connaissances.
"""

import logging
import time
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from django.core.cache import cache

from ..config import settings

logger = logging.getLogger(__name__)

# Configuration du cache
CACHE_TIMEOUT = getattr(settings, 'AI_ASSISTANT_CACHE_TIMEOUT', 3600)  # 1 heure par défaut
CACHE_ENABLED = getattr(settings, 'AI_ASSISTANT_CACHE_ENABLED', True)
EMBEDDING_MODEL = getattr(settings, 'AI_ASSISTANT_EMBEDDING_MODEL', 'text-embedding-ada-002')
EMBEDDING_DIMENSION = getattr(settings, 'AI_ASSISTANT_EMBEDDING_DIMENSION', 768)


def generate_embedding(text: str, api_key: str = None, use_cache: bool = True) -> Optional[List[float]]:
    """
    Génère un embedding vectoriel pour le texte donné.
    
    Args:
        text: Texte pour lequel générer un embedding
        api_key: Clé API OpenAI (optionnel, utilise la clé par défaut si non spécifiée)
        use_cache: Indique si le cache doit être utilisé
        
    Returns:
        Liste des valeurs de l'embedding ou None en cas d'erreur
    """
    # Vérifier si l'embedding est dans le cache
    if CACHE_ENABLED and use_cache:
        cache_key = f"embedding:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"
        cached_embedding = cache.get(cache_key)
        if cached_embedding:
            logger.debug("Embedding récupéré du cache")
            return cached_embedding
    
    try:
        # Import tardif pour éviter une dépendance au niveau du module
        from openai import OpenAI
        
        # Utiliser la clé API fournie ou celle par défaut
        if not api_key:
            api_key = getattr(settings, 'DEFAULT_AI_API_KEY', None)
            
        if not api_key:
            logger.warning("Clé API manquante pour les embeddings")
            return None
            
        # Initialiser le client OpenAI
        client = OpenAI(api_key=api_key)
        
        # Limiter la taille du texte pour éviter les dépassements de tokens
        max_text_length = 8000
        if len(text) > max_text_length:
            text = text[:max_text_length]
            
        # Mesurer le temps de génération
        start_time = time.time()
        
        # Générer l'embedding via l'API OpenAI
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL
        )
        
        # Extraire l'embedding
        embedding = response.data[0].embedding
        
        # Mettre en cache l'embedding
        if CACHE_ENABLED and use_cache:
            cache.set(cache_key, embedding, CACHE_TIMEOUT)
        
        generation_time = time.time() - start_time
        logger.debug(f"Embedding généré en {generation_time:.3f}s")
        
        return embedding
        
    except Exception as e:
        logger.exception(f"Erreur lors de la génération de l'embedding: {e}")
        return None


def cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    """
    Calcule la similarité cosinus entre deux vecteurs.
    
    Args:
        vector_a: Premier vecteur
        vector_b: Deuxième vecteur
        
    Returns:
        Score de similarité cosinus (entre -1 et 1)
    """
    try:
        # Convertir en tableaux numpy pour le calcul vectorisé
        a = np.array(vector_a)
        b = np.array(vector_b)
        
        # Calculer la similarité cosinus
        similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        return float(similarity)
    except Exception as e:
        logger.exception(f"Erreur lors du calcul de la similarité cosinus: {e}")
        return 0.0


def find_closest_embeddings(
    query_embedding: List[float],
    embeddings: List[List[float]],
    threshold: float = 0.7,
    top_k: int = 5
) -> List[Tuple[int, float]]:
    """
    Trouve les embeddings les plus proches du vecteur de requête.
    
    Args:
        query_embedding: Embedding de la requête
        embeddings: Liste des embeddings à comparer
        threshold: Seuil minimal de similarité
        top_k: Nombre maximum de résultats à retourner
        
    Returns:
        Liste de tuples (index, score) des embeddings les plus proches
    """
    similarities = []
    
    # Calculer la similarité avec chaque embedding
    for i, embedding in enumerate(embeddings):
        similarity = cosine_similarity(query_embedding, embedding)
        if similarity >= threshold:
            similarities.append((i, similarity))
    
    # Trier par similarité décroissante et limiter aux top_k résultats
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]


def get_similar_chunks(
    query: str,
    chunks: List[str],
    api_key: str = None,
    threshold: float = 0.7,
    top_k: int = 5
) -> List[Tuple[int, float, str]]:
    """
    Trouve les chunks de texte les plus similaires à la requête.
    
    Args:
        query: Requête textuelle
        chunks: Liste des chunks de texte à comparer
        api_key: Clé API OpenAI (optionnel)
        threshold: Seuil minimal de similarité
        top_k: Nombre maximum de résultats à retourner
        
    Returns:
        Liste de tuples (index, score, chunk) des chunks les plus similaires
    """
    # Générer l'embedding pour la requête
    query_embedding = generate_embedding(query, api_key)
    if not query_embedding:
        logger.warning("Impossible de générer l'embedding pour la requête")
        return []
    
    # Générer les embeddings pour chaque chunk
    chunk_embeddings = []
    for chunk in chunks:
        embedding = generate_embedding(chunk, api_key)
        if embedding:
            chunk_embeddings.append(embedding)
        else:
            # Placeholder pour maintenir l'alignement avec les chunks
            chunk_embeddings.append([0.0] * EMBEDDING_DIMENSION)
    
    # Trouver les chunks les plus similaires
    similarities = find_closest_embeddings(query_embedding, chunk_embeddings, threshold, top_k)
    
    # Construire les résultats avec les chunks correspondants
    results = []
    for idx, score in similarities:
        results.append((idx, score, chunks[idx]))
    
    return results


def bulk_generate_embeddings(texts: List[str], api_key: str = None) -> List[Optional[List[float]]]:
    """
    Génère des embeddings pour une liste de textes.
    
    Args:
        texts: Liste des textes pour lesquels générer des embeddings
        api_key: Clé API OpenAI (optionnel)
        
    Returns:
        Liste des embeddings générés (None en cas d'erreur pour un texte)
    """
    embeddings = []
    
    # Générer l'embedding pour chaque texte
    for text in texts:
        embedding = generate_embedding(text, api_key)
        embeddings.append(embedding)
    
    return embeddings 