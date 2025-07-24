"""
Module de gestion des réponses HTTP.

Ce module fournit une classe ResponseHandler qui gère le traitement
des réponses HTTP reçues des API externes.
"""

import json
import logging
from typing import Any, Dict, Optional, Union, TypeVar, Generic, Type
from requests import Response
from requests.exceptions import JSONDecodeError

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ResponseHandler:
    """
    Gestionnaire de réponses HTTP.
    
    Cette classe encapsule la logique de traitement des réponses HTTP,
    y compris la validation des codes d'état, l'extraction des données
    et la gestion des erreurs.
    """
    
    @staticmethod
    def validate_status_code(response: Response, expected_codes: list[int] = None) -> bool:
        """
        Valide le code d'état HTTP d'une réponse.
        
        Args:
            response: Réponse HTTP à valider
            expected_codes: Liste des codes d'état attendus (par défaut [200])
            
        Returns:
            True si le code d'état est valide, False sinon
        """
        if expected_codes is None:
            expected_codes = [200]
            
        if response.status_code not in expected_codes:
            logger.warning(
                f"Code d'état inattendu: {response.status_code}, "
                f"attendu: {expected_codes}, URL: {response.url}"
            )
            return False
            
        return True
    
    @staticmethod
    def extract_json(response: Response) -> Dict[str, Any]:
        """
        Extrait les données JSON d'une réponse HTTP.
        
        Args:
            response: Réponse HTTP
            
        Returns:
            Données JSON extraites
            
        Raises:
            JSONDecodeError: Si la réponse ne contient pas de JSON valide
        """
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Erreur lors du décodage JSON: {str(e)}, contenu: {response.text[:200]}")
            raise
    
    @staticmethod
    def extract_data(response: Response, data_key: Optional[str] = None) -> Any:
        """
        Extrait les données d'une réponse HTTP, avec possibilité de cibler une clé spécifique.
        
        Args:
            response: Réponse HTTP
            data_key: Clé optionnelle pour extraire une partie spécifique des données
            
        Returns:
            Données extraites
        """
        data = ResponseHandler.extract_json(response)
        
        if data_key is not None and data_key in data:
            return data[data_key]
            
        return data
    
    @staticmethod
    def handle_error_response(response: Response) -> Dict[str, Any]:
        """
        Traite une réponse d'erreur HTTP.
        
        Args:
            response: Réponse HTTP d'erreur
            
        Returns:
            Informations d'erreur structurées
        """
        try:
            error_data = response.json()
        except JSONDecodeError:
            error_data = {"message": response.text}
            
        return {
            "status_code": response.status_code,
            "error": error_data,
            "url": response.url
        }
    
    @staticmethod
    def process_response(
        response: Response, 
        expected_codes: list[int] = None,
        data_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Traite une réponse HTTP complète.
        
        Args:
            response: Réponse HTTP
            expected_codes: Liste des codes d'état attendus
            data_key: Clé optionnelle pour extraire une partie spécifique des données
            
        Returns:
            Données traitées ou informations d'erreur
        """
        if ResponseHandler.validate_status_code(response, expected_codes):
            return {
                "success": True,
                "data": ResponseHandler.extract_data(response, data_key),
                "status_code": response.status_code
            }
        else:
            error_info = ResponseHandler.handle_error_response(response)
            return {
                "success": False,
                **error_info
            } 