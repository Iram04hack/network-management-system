"""
Améliorateur de descriptions Swagger pour api_views.
"""

import re
from pathlib import Path


class SwaggerDescriptionImprover:
    """Améliorateur de descriptions Swagger."""
    
    def __init__(self):
        self.files_modified = []
        self.improvements_count = 0
        
        # Descriptions spécifiques par endpoint
        self.specific_descriptions = {
            # Dashboard endpoints
            'bulk_create.*tableau de bord': "Crée plusieurs tableaux de bord simultanément avec validation des données et gestion d'erreurs par batch.",
            'duplicate.*tableau de bord': "Crée une copie complète du tableau de bord avec possibilité de personnaliser le nom et la description.",
            'data.*tableau de bord': "Récupère les données temps réel du widget avec mise en cache et optimisations de performance.",
            'templates.*tableau de bord': "Liste tous les modèles de widgets pré-configurés avec aperçus et exemples d'utilisation.",
            
            # Device Management endpoints  
            'bulk_create.*équipement réseau': "Importe plusieurs équipements simultanément via CSV ou auto-découverte avec validation complète.",
            'bulk_delete.*équipement réseau': "Supprime plusieurs équipements sélectionnés avec vérification des dépendances.",
            'create_device_old.*équipement réseau': "Méthode héritée de création d'équipement maintenue pour compatibilité.",
            
            # Search endpoints
            'search.*recherche globale': "Effectue une recherche intelligente à travers tous les types de ressources avec suggestions.",
            'suggestions.*recherche globale': "Fournit des suggestions de recherche contextuelles basées sur l'historique utilisateur.",
            'filters.*recherche globale': "Récupère la liste complète des filtres applicables par type de ressource.",
            'search_devices.*recherche globale': "Recherche avancée dans les équipements réseau avec filtres multiples.",
            'search_alerts.*recherche globale': "Recherche intelligente dans les alertes avec filtrage par sévérité et période.",
            'search_topologies.*recherche globale': "Recherche dans les topologies découvertes avec filtres géographiques.",
            'search_configurations.*recherche globale': "Recherche textuelle avancée dans les configurations avec expressions régulières.",
            'clear.*recherche globale': "Supprime définitivement tout l'historique de recherche pour conformité RGPD.",
            
            # Topology endpoints
            'start.*découverte de topologie': "Lance l'exécution du processus de découverte avec monitoring temps réel.",
            'stop.*découverte de topologie': "Interrompt proprement le processus en cours en sauvegardant les résultats partiels.",
            'status.*découverte de topologie': "Récupère l'état actuel : progression, équipements trouvés, erreurs et temps estimé.",
            'export.*découverte de topologie': "Exporte les résultats dans différents formats avec métadonnées complètes.",
            
            # Prometheus endpoints
            'query.*métrique Prometheus': "Exécute une requête PromQL en temps réel avec support des fonctions d'agrégation.",
            'query_range.*métrique Prometheus': "Exécute une requête PromQL sur plage temporelle pour analyse historique.",
            'targets.*métrique Prometheus': "Liste toutes les cibles de scraping avec leurs statuts de santé.",
            'alerts.*métrique Prometheus': "Récupère toutes les alertes en cours avec niveaux de sévérité et actions recommandées.",
            'status.*métrique Prometheus': "Vérifie la santé du service : version, uptime, performance et statistiques.",
            
            # Grafana endpoints
            'setup.*dashboard Grafana': "Configure automatiquement Grafana avec sources de données et dashboards par défaut.",
            'status.*dashboard Grafana': "Vérifie la connectivité et santé du service avec informations de version.",
            
            # Security endpoints
            'status.*configuration Fail2ban': "Vérifie le statut du service avec statistiques globales et santé des jails.",
            'ban_ip.*configuration Fail2ban': "Ajoute une adresse IP à la liste de bannissement avec durée configurable.",
            'unban_ip.*configuration Fail2ban': "Retire une adresse IP de la liste de bannissement et restaure l'accès.",
            'banned.*configuration Fail2ban': "Récupère toutes les IPs bannies avec détails des violations et durées restantes.",
            'alerts.*configuration Fail2ban': "Récupère les alertes de sécurité détectées avec détails des attaques.",
            'add_rule.*configuration Fail2ban': "Ajoute et active immédiatement une nouvelle règle sans redémarrage.",
            'reload.*configuration Fail2ban': "Recharge toutes les règles depuis les fichiers de configuration.",
        }
        
        # Descriptions génériques améliorées par action
        self.action_templates = {
            'list': "Récupère la liste complète des {resource} avec filtrage, tri et pagination avancée.",
            'create': "Crée un nouveau {resource} avec validation des données et configuration automatique.",
            'retrieve': "Récupère les détails complets d'un {resource} spécifique avec données temps réel.",
            'update': "Met à jour un {resource} existant avec validation des changements et historique.",
            'partial_update': "Met à jour partiellement un {resource} avec validation des champs modifiés.",
            'destroy': "Supprime définitivement un {resource} après vérification des dépendances.",
            'get': "Récupère les informations détaillées avec données temps réel et métriques associées.",
            'post': "Exécute une opération avec validation des données et traitement sécurisé.",
            'put': "Met à jour complètement la ressource avec vérification des permissions d'accès.",
            'patch': "Applique des modifications partielles avec validation et audit des changements.",
            'delete': "Supprime la ressource avec sauvegarde préalable et vérification des dépendances.",
        }
    
    def improve_all_descriptions(self):
        """Améliore toutes les descriptions Swagger."""
        print("🔧 === AMÉLIORATION DES DESCRIPTIONS SWAGGER ===\n")
        
        view_files = [
            'dashboard_views.py',
            'device_management_views.py', 
            'search_views.py',
            'topology_discovery_views.py',
            'prometheus_views.py',
            'grafana_views.py',
            'security_views.py'
        ]
        
        base_path = Path(__file__).parent.parent / "views"
        
        for file_name in view_files:
            file_path = base_path / file_name
            if file_path.exists():
                print(f"📝 Amélioration de {file_name}...")
                self._improve_file_descriptions(file_path)
            else:
                print(f"⚠️ Fichier non trouvé: {file_name}")
        
        self._print_summary()
    
    def _improve_file_descriptions(self, file_path: Path):
        """Améliore les descriptions dans un fichier."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Remplacer les descriptions génériques
            content = self._replace_generic_descriptions(content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.files_modified.append(str(file_path))
                print(f"  ✅ {file_path.name} amélioré")
            else:
                print(f"  ℹ️ {file_path.name} déjà optimal")
                
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
    
    def _replace_generic_descriptions(self, content: str) -> str:
        """Remplace les descriptions génériques."""
        # Pattern pour les descriptions génériques
        pattern = r'operation_description="Exécute l\'action (\w+) sur ([^"]+)\."'
        
        def replace_func(match):
            action = match.group(1)
            resource = match.group(2)
            
            # Chercher une description spécifique
            for key, desc in self.specific_descriptions.items():
                if re.search(key, f"{action}.*{resource}"):
                    self.improvements_count += 1
                    return f'operation_description="{desc}"'
            
            # Utiliser template générique amélioré
            if action in self.action_templates:
                improved_desc = self.action_templates[action].format(resource=resource)
            else:
                improved_desc = f"Effectue l'opération {action} sur {resource} avec traitement sécurisé et validation des données."
            
            self.improvements_count += 1
            return f'operation_description="{improved_desc}"'
        
        return re.sub(pattern, replace_func, content)
    
    def _print_summary(self):
        """Affiche le résumé."""
        print("\n" + "="*60)
        print("📊 === RÉSUMÉ DES AMÉLIORATIONS ===")
        print("="*60)
        
        print(f"\n✨ **AMÉLIORATIONS APPLIQUÉES**")
        print(f"  • Descriptions améliorées: {self.improvements_count}")
        print(f"  • Fichiers modifiés: {len(self.files_modified)}")
        
        if self.files_modified:
            print(f"\n📝 **FICHIERS AMÉLIORÉS**")
            for file_path in self.files_modified:
                print(f"  • {Path(file_path).name}")
        
        print(f"\n🎯 **RÉSULTAT**")
        print(f"  • Descriptions spécifiques et informatives")
        print(f"  • Documentation professionnelle en français")
        print(f"  • Terminologie technique précise")
        
        print(f"\n✅ Amélioration terminée!")


def main():
    """Point d'entrée principal."""
    improver = SwaggerDescriptionImprover()
    improver.improve_all_descriptions()


if __name__ == "__main__":
    main()
 