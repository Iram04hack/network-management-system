"""
Sérialiseurs pour les commandes.

Ce module contient les sérialiseurs pour convertir les modèles
de commande en représentations JSON pour l'API.
"""

from rest_framework import serializers


class CommandResultSerializer(serializers.Serializer):
    """Sérialiseur pour les résultats de commande."""
    
    command = serializers.CharField()
    exit_code = serializers.IntegerField()
    stdout = serializers.CharField()
    stderr = serializers.CharField()
    success = serializers.BooleanField()


class CommandRequestSerializer(serializers.Serializer):
    """Sérialiseur pour les requêtes de commande."""
    
    command = serializers.CharField()
    command_type = serializers.ChoiceField(choices=['shell', 'sql', 'python'], default='shell')
    
    # Paramètres spécifiques pour SQL
    database_path = serializers.CharField(required=False)
    
    def validate(self, data):
        """Valide les données de la requête."""
        command_type = data.get('command_type')
        
        if command_type == 'sql' and 'database_path' not in data:
            data['database_path'] = ':memory:'  # Valeur par défaut pour SQLite
        
        return data 