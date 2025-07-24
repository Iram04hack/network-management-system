"""
Service d'automatisation GNS3 amélioré pour les opérations avancées sur les topologies.
"""
import logging
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
import paramiko
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from gns3_integration.domain.interfaces import GNS3AutomationService
from gns3_integration.domain.interfaces import GNS3ClientPort
from gns3_integration.models import Project, Node, Script, ScriptExecution, Snapshot, Workflow, WorkflowExecution
from api_clients.network.configuration_management import ConfigurationVersionRepository

logger = logging.getLogger(__name__)

class GNS3AutomationServiceImpl(GNS3AutomationService):
    """
    Implémentation du service d'automatisation GNS3 pour la gestion
    de scripts, configurations, snapshots et workflows.
    """
    
    def __init__(self, gns3_client: GNS3ClientPort, config_version_repo: ConfigurationVersionRepository = None):
        """
        Initialise le service d'automatisation.
        
        Args:
            gns3_client: Client API GNS3
            config_version_repo: Référentiel de gestion des configurations versionnées
        """
        self.gns3_client = gns3_client
        self.config_version_repo = config_version_repo or ConfigurationVersionRepository()
        
        # Charges les configurations par défaut depuis settings.py ou variables d'environnement
        self.default_ssh_credentials = {
            'username': getattr(settings, 'GNS3_DEFAULT_SSH_USERNAME', ''),
            'password': getattr(settings, 'GNS3_DEFAULT_SSH_PASSWORD', ''),
        }
        
        # Spécificité par type de nœud (peut être configuré dans settings.py)
        self.node_specific_credentials = getattr(settings, 'GNS3_NODE_CREDENTIALS', {})
    
    def execute_script(self, project_id: str, node_id: str, script: str, credentials: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Exécute un script sur un nœud GNS3.
        
        Args:
            project_id: Identifiant du projet GNS3
            node_id: Identifiant du nœud sur lequel exécuter le script
            script: Script à exécuter
            credentials: Credentials optionnels pour l'exécution du script
            
        Returns:
            Résultat de l'exécution du script
        """
        try:
            # Récupérer le projet et le nœud
            project = Project.objects.get(project_id=project_id)
            node = Node.objects.get(project=project, node_id=node_id)
            
            # Démarrer le nœud s'il n'est pas déjà démarré
            if node.status != "started":
                start_result = self.gns3_client.start_node(project_id, node_id)
                if not start_result or 'success' not in start_result:
                    return {"error": "Impossible de démarrer le nœud"}
                node.refresh_from_db()
            
            # Récupérer la console du nœud
            console_info = self.gns3_client.get_node_console(project_id, node_id)
            if not console_info or 'console_host' not in console_info or 'console_port' not in console_info:
                return {"error": "Impossible d'obtenir les informations de console du nœud"}
            
            console_host = console_info['console_host']
            console_port = console_info['console_port']
            
            # Créer une exécution de script dans la base de données
            script_execution = ScriptExecution.objects.create(
                script=None,  # Script direct, pas depuis la base de données
                project=project,
                node=node,
                status='running',
                start_time=datetime.now()
            )
            
            # Exécuter le script via SSH
            success, output, error = self._execute_via_ssh(
                node_type=node.node_type,
                console_host=console_host,
                console_port=console_port,
                script=script,
                credentials=credentials
            )
            
            # Mettre à jour l'exécution du script
            script_execution.status = 'completed' if success else 'failed'
            script_execution.output = output
            script_execution.error_message = error
            script_execution.end_time = datetime.now()
            script_execution.save()
            
            return {
                "success": success,
                "output": output,
                "error": error if not success else ""
            }
            
        except ObjectDoesNotExist as e:
            logger.error(f"Erreur lors de l'exécution du script: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du script: {e}")
            return {"error": f"Erreur d'exécution: {str(e)}"}
    
    def deploy_configuration(self, project_id: str, node_id: str, configuration_id: int) -> Dict[str, Any]:
        """
        Déploie une configuration sur un nœud GNS3.
        
        Args:
            project_id: Identifiant du projet GNS3
            node_id: Identifiant du nœud
            configuration_id: Identifiant de la configuration à déployer
            
        Returns:
            Résultat du déploiement
        """
        try:
            # Récupérer le projet et le nœud
            project = Project.objects.get(project_id=project_id)
            node = Node.objects.get(project=project, node_id=node_id)
            
            # Récupérer la configuration depuis le référentiel de configurations
            configuration = self.config_version_repo.get_configuration_version(configuration_id)
            if not configuration or 'content' not in configuration:
                return {"error": "Configuration non trouvée ou invalide"}
            
            # Déployer la configuration via un script
            deploy_script = self._get_deploy_script(node.node_type, configuration['content'])
            if not deploy_script:
                return {"error": f"Type de nœud non supporté pour le déploiement de configuration: {node.node_type}"}
            
            # Exécuter le script de déploiement
            return self.execute_script(project_id, node_id, deploy_script)
            
        except ObjectDoesNotExist as e:
            logger.error(f"Erreur lors du déploiement de la configuration: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Erreur lors du déploiement de la configuration: {e}")
            return {"error": f"Erreur de déploiement: {str(e)}"}
    
    def create_snapshot(self, project_id: str, name: str = None) -> Dict[str, Any]:
        """
        Crée un snapshot d'un projet GNS3.
        
        Args:
            project_id: Identifiant du projet GNS3
            name: Nom du snapshot (optionnel)
            
        Returns:
            Informations sur le snapshot créé
        """
        try:
            # Récupérer le projet
            project = Project.objects.get(project_id=project_id)
            
            # Créer un nom par défaut si non spécifié
            if not name:
                name = f"Snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Créer le snapshot via l'API GNS3
            snapshot_result = self.gns3_client.create_snapshot(project_id, name)
            if not snapshot_result or 'snapshot_id' not in snapshot_result:
                return {"error": "Impossible de créer le snapshot"}
            
            # Enregistrer le snapshot dans la base de données
            snapshot = Snapshot.objects.create(
                project=project,
                name=name,
                snapshot_id=snapshot_result['snapshot_id']
            )
            
            return {
                "success": True,
                "snapshot_id": snapshot.snapshot_id,
                "name": snapshot.name,
                "created_at": snapshot.created_at.isoformat()
            }
            
        except ObjectDoesNotExist as e:
            logger.error(f"Erreur lors de la création du snapshot: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Erreur lors de la création du snapshot: {e}")
            return {"error": f"Erreur de snapshot: {str(e)}"}
    
    def restore_snapshot(self, project_id: str, snapshot_id: str) -> bool:
        """
        Restaure un snapshot d'un projet GNS3.
        
        Args:
            project_id: Identifiant du projet GNS3
            snapshot_id: Identifiant du snapshot à restaurer
            
        Returns:
            True si restauration réussie, False sinon
        """
        try:
            # Récupérer le projet et le snapshot
            project = Project.objects.get(project_id=project_id)
            snapshot = Snapshot.objects.get(project=project, snapshot_id=snapshot_id)
            
            # Restaurer le snapshot via l'API GNS3
            restore_result = self.gns3_client.restore_snapshot(project_id, snapshot_id)
            if not restore_result or not restore_result.get('success', False):
                return False
            
            # Mettre à jour l'état du projet et synchroniser les données
            project.status = "open"
            project.save()
            
            return True
            
        except ObjectDoesNotExist:
            logger.error(f"Projet ou snapshot non trouvé: {project_id}, {snapshot_id}")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la restauration du snapshot: {e}")
            return False
    
    def run_workflow(self, project_id: str, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute un workflow sur un projet GNS3.
        
        Args:
            project_id: Identifiant du projet GNS3
            workflow_data: Données du workflow à exécuter
            
        Returns:
            Résultat de l'exécution du workflow
        """
        workflow_execution = None
        try:
            # Récupérer le projet
            project = Project.objects.get(project_id=project_id)
            
            # Créer ou récupérer le workflow
            workflow_id = workflow_data.get('workflow_id')
            workflow = None
            
            if workflow_id:
                # Utiliser un workflow existant
                workflow = Workflow.objects.get(id=workflow_id)
            else:
                # Créer un workflow temporaire pour cette exécution
                workflow_name = workflow_data.get('name', f"Workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                workflow = Workflow.objects.create(
                    name=workflow_name,
                    steps=workflow_data.get('steps', []),
                    is_template=False
                )
            
            # Créer une exécution de workflow
            workflow_execution = WorkflowExecution.objects.create(
                workflow=workflow,
                project=project,
                status='running',
                parameters=workflow_data.get('parameters', {}),
                start_time=datetime.now()
            )
            
            # Exécuter les étapes du workflow
            results = []
            
            for i, step in enumerate(workflow.steps):
                step_type = step.get('type')
                step_parameters = step.get('parameters', {})
                
                # Exécuter l'étape en fonction de son type
                if step_type == 'script':
                    node_id = step_parameters.get('node_id')
                    script = step_parameters.get('script')
                    
                    if node_id and script:
                        step_result = self.execute_script(project_id, node_id, script)
                        if not step_result or 'error' in step_result:
                            raise Exception(f"Échec à l'étape {i+1}: {step_result.get('error', 'Erreur inconnue')}")
                        
                        results.append({
                            "step": i+1,
                            "type": step_type,
                            "result": step_result
                        })
                
                elif step_type == 'deploy_config':
                    node_id = step_parameters.get('node_id')
                    config_id = step_parameters.get('configuration_id')
                    
                    if node_id and config_id:
                        step_result = self.deploy_configuration(project_id, node_id, config_id)
                        if not step_result or 'error' in step_result:
                            raise Exception(f"Échec à l'étape {i+1}: {step_result.get('error', 'Erreur inconnue')}")
                        
                        results.append({
                            "step": i+1,
                            "type": step_type,
                            "result": step_result
                        })
                
                else:
                    raise Exception(f"Type d'étape non supporté: {step_type}")
            
            # Mettre à jour l'exécution du workflow
            workflow_execution.status = 'completed'
            workflow_execution.results = results
            workflow_execution.end_time = datetime.now()
            workflow_execution.save()
            
            return {
                "success": True,
                "workflow_id": workflow.id,
                "execution_id": workflow_execution.id,
                "results": results
            }
            
        except ObjectDoesNotExist as e:
            if workflow_execution:
                workflow_execution.status = 'failed'
                workflow_execution.error_message = str(e)
                workflow_execution.end_time = datetime.now()
                workflow_execution.save()
            
            logger.error(f"Erreur lors de l'exécution du workflow: {e}")
            return {"error": str(e)}
        except Exception as e:
            if workflow_execution:
                workflow_execution.status = 'failed'
                workflow_execution.error_message = str(e)
                workflow_execution.end_time = datetime.now()
                workflow_execution.save()
            
            logger.error(f"Erreur lors de l'exécution du workflow: {e}")
            return {"error": f"Erreur d'exécution: {str(e)}"}
    
    def export_topology(self, project_id: str, export_format: str = "json") -> Dict[str, Any]:
        """
        Exporte une topologie GNS3 dans un format spécifié.
        
        Args:
            project_id: Identifiant du projet GNS3
            export_format: Format d'exportation (json, yaml, etc.)
            
        Returns:
            Données de la topologie exportée
        """
        try:
            # Récupérer le projet
            project = Project.objects.get(project_id=project_id)
            
            # Récupérer les nœuds et liens du projet
            nodes = Node.objects.filter(project=project)
            links = project.links.all()
            
            # Construire la représentation de la topologie
            topology = {
                "project": {
                    "id": project.project_id,
                    "name": project.name,
                    "description": project.description
                },
                "nodes": [
                    {
                        "id": node.node_id,
                        "name": node.name,
                        "type": node.node_type,
                        "x": node.x_position,
                        "y": node.y_position,
                        "properties": node.properties
                    }
                    for node in nodes
                ],
                "links": [
                    {
                        "id": link.link_id,
                        "source": {
                            "node_id": link.source_node.node_id,
                            "port": link.source_port
                        },
                        "target": {
                            "node_id": link.target_node.node_id,
                            "port": link.target_port
                        }
                    }
                    for link in links
                ]
            }
            
            # Convertir au format demandé
            if export_format.lower() == "json":
                return topology
            else:
                return {"error": f"Format d'exportation non supporté: {export_format}"}
            
        except ObjectDoesNotExist as e:
            logger.error(f"Erreur lors de l'exportation de la topologie: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation de la topologie: {e}")
            return {"error": f"Erreur d'exportation: {str(e)}"}
    
    def import_topology(self, topology_data: Dict[str, Any], name: str = None) -> Dict[str, Any]:
        """
        Importe une topologie GNS3.
        
        Args:
            topology_data: Données de la topologie à importer
            name: Nom à donner à la topologie importée (optionnel)
            
        Returns:
            Informations sur la topologie importée
        """
        try:
            # Créer un nouveau projet
            project_name = name or topology_data.get("project", {}).get("name") or f"Imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            project_data = self.gns3_client.create_project(project_name)
            if not project_data or 'project_id' not in project_data:
                return {"error": "Échec de la création du projet."}
            
            new_project_id = project_data['project_id']
            
            # Créer les nœuds
            nodes_mapping = {}  # Mapping entre anciens et nouveaux IDs
            
            for node_data in topology_data.get("nodes", []):
                new_node = self.gns3_client.create_node(
                    project_id=new_project_id,
                    node_type=node_data.get("type"),
                    name=node_data.get("name"),
                    x=node_data.get("x", 0),
                    y=node_data.get("y", 0),
                    properties=node_data.get("properties", {})
                )
                
                if new_node and 'node_id' in new_node:
                    nodes_mapping[node_data.get("id")] = new_node['node_id']
            
            # Créer les liens
            links_created = []
            
            for link_data in topology_data.get("links", []):
                source_id = link_data.get("source", {}).get("node_id")
                target_id = link_data.get("target", {}).get("node_id")
                
                if source_id in nodes_mapping and target_id in nodes_mapping:
                    new_source_id = nodes_mapping[source_id]
                    new_target_id = nodes_mapping[target_id]
                    
                    source_port = link_data.get("source", {}).get("port", {})
                    target_port = link_data.get("target", {}).get("port", {})
                    
                    # Adapter les ports si nécessaire
                    new_link = self.gns3_client.create_link(
                        project_id=new_project_id,
                        source_node_id=new_source_id,
                        source_port=source_port.get("port_number", 0),
                        target_node_id=new_target_id,
                        target_port=target_port.get("port_number", 0)
                    )
                    
                    if new_link and 'link_id' in new_link:
                        links_created.append(new_link['link_id'])
            
            return {
                "success": True,
                "project_id": new_project_id,
                "project_name": project_name,
                "nodes_count": len(nodes_mapping),
                "links_count": len(links_created)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'importation de la topologie: {e}")
            return {"error": f"Erreur d'importation: {str(e)}"}
    
    def _execute_via_ssh(self, node_type: str, console_host: str, 
                         console_port: int, script: str, 
                         credentials: Dict[str, str] = None) -> Tuple[bool, str, str]:
        """
        Exécute un script sur un nœud via SSH.
        
        Args:
            node_type: Type de nœud
            console_host: Hôte de la console
            console_port: Port de la console
            script: Script à exécuter
            credentials: Informations d'identification SSH optionnelles
            
        Returns:
            Tuple (succès, sortie, erreur)
        """
        try:
            # Déterminer les credentials à utiliser
            # 1. Credentials fournis explicitement
            # 2. Credentials spécifiques au type de nœud
            # 3. Credentials par défaut
            # 4. Valeurs de secours (Non recommandé, uniquement pour compatibilité)
            
            if not credentials:
                credentials = {}
            
            username = (credentials.get('username') or 
                       self.node_specific_credentials.get(node_type, {}).get('username') or
                       self.default_ssh_credentials.get('username') or
                       "")
            
            password = (credentials.get('password') or 
                       self.node_specific_credentials.get(node_type, {}).get('password') or
                       self.default_ssh_credentials.get('password') or
                       "")
            
            if not username or not password:
                raise ValueError("SSH credentials requis mais non configurés")
                
            # Créer une connexion SSH
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Se connecter à la console
            client.connect(
                hostname=console_host,
                port=console_port,
                username=username,
                password=password,
                timeout=10
            )
            
            # Exécuter le script
            stdin, stdout, stderr = client.exec_command(script)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            # Fermer la connexion
            client.close()
            
            return (error == "", output, error)
            
        except Exception as e:
            logger.error(f"Erreur d'exécution SSH: {e}")
            return (False, "", str(e))
    
    def _get_deploy_script(self, node_type: str, configuration: str) -> Optional[str]:
        """
        Génère un script de déploiement de configuration selon le type de nœud.
        
        Args:
            node_type: Type de nœud
            configuration: Contenu de la configuration
            
        Returns:
            Script de déploiement ou None si type non supporté
        """
        if node_type == "dynamips":
            # Pour routeurs Cisco
            return f"""
                config t
                {configuration}
                end
                write memory
                """
        elif node_type == "qemu":
            # Selon l'OS du nœud QEMU, à adapter
            return f"""
                sudo bash -c 'cat > /etc/network/interfaces << EOF
                {configuration}
                EOF'
                sudo systemctl restart networking
                """
        elif node_type in ["docker", "vpcs"]:
            # Pour containers Docker ou VPCS
            return configuration
        else:
            # Type non supporté
            return None 