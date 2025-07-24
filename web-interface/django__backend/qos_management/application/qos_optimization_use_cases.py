"""
Cas d'utilisation pour l'optimisation automatique des politiques QoS.

Ce module implémente des algorithmes d'apprentissage automatique et d'optimisation
adaptatifs pour améliorer automatiquement les performances QoS.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
from collections import deque

from ..domain.interfaces import (
    QoSPolicyRepository,
    QoSMonitoringService,
    TrafficClassificationService
)
from ..domain.exceptions import QoSOptimizationException

logger = logging.getLogger(__name__)


class OptimizationStrategy(str, Enum):
    """Stratégies d'optimisation disponibles."""
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    GENETIC_ALGORITHM = "genetic_algorithm"
    GRADIENT_DESCENT = "gradient_descent"
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"


@dataclass
class QoSMetrics:
    """Métriques QoS pour l'optimisation."""
    latency: float
    jitter: float
    packet_loss: float
    throughput: float
    utilization: float
    timestamp: datetime
    
    def to_vector(self) -> np.ndarray:
        """Convertit les métriques en vecteur numpy."""
        return np.array([self.latency, self.jitter, self.packet_loss, 
                        self.throughput, self.utilization])


@dataclass
class OptimizationAction:
    """Action d'optimisation à appliquer."""
    policy_id: int
    parameter_changes: Dict[str, Any]
    expected_improvement: float
    confidence: float
    strategy_used: OptimizationStrategy


@dataclass
class OptimizationResult:
    """Résultat d'une optimisation."""
    success: bool
    improvement_score: float
    metrics_before: QoSMetrics
    metrics_after: QoSMetrics
    actions_taken: List[OptimizationAction]
    timestamp: datetime
    details: str


class QoSOptimizationUseCase:
    """
    Cas d'utilisation principal pour l'optimisation automatique QoS.
    """
    
    def __init__(
        self,
        qos_policy_repository: QoSPolicyRepository,
        qos_monitoring_service: QoSMonitoringService,
        traffic_classification_service: TrafficClassificationService
    ):
        self.qos_policy_repository = qos_policy_repository
        self.qos_monitoring_service = qos_monitoring_service
        self.traffic_classification_service = traffic_classification_service
        
        # Optimizers pour différentes stratégies
        self.rl_optimizer = ReinforcementLearningOptimizer()
        self.genetic_optimizer = GeneticAlgorithmOptimizer()
        self.rule_optimizer = RuleBasedOptimizer()
        
        # Historique des optimisations
        self.optimization_history = deque(maxlen=1000)
        self.performance_baseline = {}
    
    def execute_optimization(
        self,
        policy_id: int,
        strategy: OptimizationStrategy = OptimizationStrategy.HYBRID,
        target_improvement: float = 0.1
    ) -> OptimizationResult:
        """
        Exécute une optimisation automatique d'une politique QoS.
        
        Args:
            policy_id: ID de la politique à optimiser
            strategy: Stratégie d'optimisation à utiliser
            target_improvement: Amélioration cible (0.1 = 10%)
            
        Returns:
            Résultat de l'optimisation
        """
        try:
            logger.info(f"Début de l'optimisation de la politique {policy_id} avec {strategy}")
            
            # 1. Collecter les métriques actuelles
            current_metrics = self._collect_current_metrics(policy_id)
            
            # 2. Analyser les patterns de trafic
            traffic_patterns = self._analyze_traffic_patterns(policy_id)
            
            # 3. Générer des actions d'optimisation
            optimization_actions = self._generate_optimization_actions(
                policy_id, current_metrics, traffic_patterns, strategy
            )
            
            # 4. Évaluer et sélectionner la meilleure action
            best_action = self._select_best_action(optimization_actions, target_improvement)
            
            if not best_action:
                return OptimizationResult(
                    success=False,
                    improvement_score=0.0,
                    metrics_before=current_metrics,
                    metrics_after=current_metrics,
                    actions_taken=[],
                    timestamp=datetime.now(),
                    details="Aucune amélioration significative trouvée"
                )
            
            # 5. Appliquer l'action d'optimisation
            application_success = self._apply_optimization_action(best_action)
            
            if not application_success:
                return OptimizationResult(
                    success=False,
                    improvement_score=0.0,
                    metrics_before=current_metrics,
                    metrics_after=current_metrics,
                    actions_taken=[best_action],
                    timestamp=datetime.now(),
                    details="Échec de l'application de l'optimisation"
                )
            
            # 6. Attendre et mesurer l'amélioration
            await_duration = 60  # 1 minute d'attente
            logger.info(f"Attente de {await_duration}s pour mesurer l'impact...")
            
            # Simuler l'attente (dans un vrai système, utiliser time.sleep)
            new_metrics = self._collect_current_metrics(policy_id)
            
            # 7. Calculer le score d'amélioration
            improvement_score = self._calculate_improvement_score(current_metrics, new_metrics)
            
            # 8. Enregistrer le résultat
            result = OptimizationResult(
                success=improvement_score > 0,
                improvement_score=improvement_score,
                metrics_before=current_metrics,
                metrics_after=new_metrics,
                actions_taken=[best_action],
                timestamp=datetime.now(),
                details=f"Amélioration: {improvement_score:.2%}"
            )
            
            self.optimization_history.append(result)
            
            # 9. Mettre à jour les modèles d'apprentissage
            self._update_learning_models(best_action, improvement_score)
            
            logger.info(f"Optimisation terminée. Amélioration: {improvement_score:.2%}")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation: {str(e)}")
            raise QoSOptimizationException(f"Échec de l'optimisation: {str(e)}")
    
    def continuous_optimization(
        self,
        policies: List[int],
        optimization_interval: int = 300,
        improvement_threshold: float = 0.05
    ) -> None:
        """
        Lance un processus d'optimisation continue.
        
        Args:
            policies: Liste des politiques à optimiser
            optimization_interval: Intervalle entre optimisations (secondes)
            improvement_threshold: Seuil d'amélioration minimum
        """
        logger.info(f"Démarrage de l'optimisation continue pour {len(policies)} politiques")
        
        # Dans un vrai système, ceci serait une tâche asynchrone ou un thread
        for policy_id in policies:
            try:
                # Vérifier si une optimisation est nécessaire
                if self._needs_optimization(policy_id, improvement_threshold):
                    result = self.execute_optimization(
                        policy_id=policy_id,
                        strategy=OptimizationStrategy.HYBRID,
                        target_improvement=improvement_threshold
                    )
                    
                    if result.success:
                        logger.info(f"Politique {policy_id} optimisée avec succès")
                    else:
                        logger.warning(f"Optimisation de la politique {policy_id} échouée")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'optimisation continue de {policy_id}: {str(e)}")
    
    def _collect_current_metrics(self, policy_id: int) -> QoSMetrics:
        """
        Collecte les métriques actuelles pour une politique.
        
        Args:
            policy_id: ID de la politique
            
        Returns:
            Métriques QoS actuelles
        """
        # Dans un vrai système, récupérer depuis le service de monitoring
        metrics_data = self.qos_monitoring_service.get_metrics(
            device_id=1,  # Simplification
            interface_id=1,
            period="5m"
        )
        
        return QoSMetrics(
            latency=metrics_data.get('average_latency', 10.0),
            jitter=metrics_data.get('jitter', 2.0),
            packet_loss=metrics_data.get('packet_loss_rate', 0.1),
            throughput=metrics_data.get('throughput', 80.0),
            utilization=metrics_data.get('utilization', 60.0),
            timestamp=datetime.now()
        )
    
    def _analyze_traffic_patterns(self, policy_id: int) -> Dict[str, Any]:
        """
        Analyse les patterns de trafic pour une politique.
        
        Args:
            policy_id: ID de la politique
            
        Returns:
            Analyse des patterns de trafic
        """
        # Simuler l'analyse de patterns de trafic
        return {
            'dominant_applications': ['web_browsing', 'video_streaming'],
            'peak_hours': [9, 10, 11, 14, 15, 16],
            'traffic_variability': 'medium',
            'congestion_points': ['interface_1'],
            'bandwidth_trends': {
                'voice': {'trend': 'stable', 'avg_usage': 15},
                'video': {'trend': 'increasing', 'avg_usage': 45},
                'data': {'trend': 'decreasing', 'avg_usage': 40}
            }
        }
    
    def _generate_optimization_actions(
        self,
        policy_id: int,
        metrics: QoSMetrics,
        patterns: Dict[str, Any],
        strategy: OptimizationStrategy
    ) -> List[OptimizationAction]:
        """
        Génère des actions d'optimisation possibles.
        
        Args:
            policy_id: ID de la politique
            metrics: Métriques actuelles
            patterns: Patterns de trafic
            strategy: Stratégie d'optimisation
            
        Returns:
            Liste d'actions d'optimisation
        """
        actions = []
        
        if strategy in [OptimizationStrategy.REINFORCEMENT_LEARNING, OptimizationStrategy.HYBRID]:
            rl_actions = self.rl_optimizer.generate_actions(policy_id, metrics, patterns)
            actions.extend(rl_actions)
        
        if strategy in [OptimizationStrategy.GENETIC_ALGORITHM, OptimizationStrategy.HYBRID]:
            ga_actions = self.genetic_optimizer.generate_actions(policy_id, metrics, patterns)
            actions.extend(ga_actions)
        
        if strategy in [OptimizationStrategy.RULE_BASED, OptimizationStrategy.HYBRID]:
            rule_actions = self.rule_optimizer.generate_actions(policy_id, metrics, patterns)
            actions.extend(rule_actions)
        
        return actions
    
    def _select_best_action(
        self,
        actions: List[OptimizationAction],
        target_improvement: float
    ) -> Optional[OptimizationAction]:
        """
        Sélectionne la meilleure action d'optimisation.
        
        Args:
            actions: Liste d'actions possibles
            target_improvement: Amélioration cible
            
        Returns:
            Meilleure action ou None
        """
        if not actions:
            return None
        
        # Filtrer les actions avec amélioration suffisante
        viable_actions = [
            action for action in actions
            if action.expected_improvement >= target_improvement
        ]
        
        if not viable_actions:
            return None
        
        # Sélectionner l'action avec le meilleur score pondéré
        def score_action(action):
            return action.expected_improvement * action.confidence
        
        return max(viable_actions, key=score_action)
    
    def _apply_optimization_action(self, action: OptimizationAction) -> bool:
        """
        Applique une action d'optimisation.
        
        Args:
            action: Action à appliquer
            
        Returns:
            True si l'application a réussi
        """
        try:
            # Récupérer la politique actuelle
            policy = self.qos_policy_repository.get_policy(action.policy_id)
            if not policy:
                return False
            
            # Appliquer les changements de paramètres
            for param_name, new_value in action.parameter_changes.items():
                # Dans un vrai système, mettre à jour les paramètres de la politique
                logger.info(f"Changement {param_name}: {new_value}")
            
            # Sauvegarder la politique modifiée
            # self.qos_policy_repository.update_policy(policy)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application de l'action: {str(e)}")
            return False
    
    def _calculate_improvement_score(
        self,
        before: QoSMetrics,
        after: QoSMetrics
    ) -> float:
        """
        Calcule le score d'amélioration entre deux sets de métriques.
        
        Args:
            before: Métriques avant optimisation
            after: Métriques après optimisation
            
        Returns:
            Score d'amélioration (-1.0 à 1.0)
        """
        # Pondération des métriques
        weights = {
            'latency': -0.3,      # Réduction = amélioration
            'jitter': -0.2,       # Réduction = amélioration
            'packet_loss': -0.3,  # Réduction = amélioration
            'throughput': 0.15,   # Augmentation = amélioration
            'utilization': -0.05  # Réduction légère = amélioration
        }
        
        total_score = 0.0
        
        # Latence: amélioration si diminution
        if before.latency > 0:
            latency_change = (before.latency - after.latency) / before.latency
            total_score += weights['latency'] * latency_change
        
        # Jitter: amélioration si diminution
        if before.jitter > 0:
            jitter_change = (before.jitter - after.jitter) / before.jitter
            total_score += weights['jitter'] * jitter_change
        
        # Perte de paquets: amélioration si diminution
        if before.packet_loss > 0:
            loss_change = (before.packet_loss - after.packet_loss) / before.packet_loss
            total_score += weights['packet_loss'] * loss_change
        
        # Débit: amélioration si augmentation
        if before.throughput > 0:
            throughput_change = (after.throughput - before.throughput) / before.throughput
            total_score += weights['throughput'] * throughput_change
        
        # Utilisation: amélioration si légère diminution (éviter surcharge)
        if before.utilization > 0:
            util_change = (before.utilization - after.utilization) / before.utilization
            total_score += weights['utilization'] * util_change
        
        return max(-1.0, min(1.0, total_score))
    
    def _needs_optimization(self, policy_id: int, threshold: float) -> bool:
        """
        Détermine si une politique a besoin d'optimisation.
        
        Args:
            policy_id: ID de la politique
            threshold: Seuil de dégradation
            
        Returns:
            True si optimisation nécessaire
        """
        # Récupérer les métriques actuelles
        current_metrics = self._collect_current_metrics(policy_id)
        
        # Comparer avec la baseline
        baseline = self.performance_baseline.get(policy_id)
        if not baseline:
            # Première fois, établir baseline
            self.performance_baseline[policy_id] = current_metrics
            return False
        
        # Calculer la dégradation
        degradation = self._calculate_improvement_score(baseline, current_metrics)
        
        # Si dégradation significative, optimisation nécessaire
        return degradation < -threshold
    
    def _update_learning_models(self, action: OptimizationAction, improvement: float):
        """
        Met à jour les modèles d'apprentissage avec les résultats.
        
        Args:
            action: Action qui a été appliquée
            improvement: Score d'amélioration obtenu
        """
        if action.strategy_used == OptimizationStrategy.REINFORCEMENT_LEARNING:
            self.rl_optimizer.update_model(action, improvement)
        elif action.strategy_used == OptimizationStrategy.GENETIC_ALGORITHM:
            self.genetic_optimizer.update_model(action, improvement)
        
        # Mettre à jour les statistiques globales
        logger.info(f"Modèle {action.strategy_used} mis à jour avec amélioration: {improvement:.2%}")


class ReinforcementLearningOptimizer:
    """
    Optimiseur basé sur l'apprentissage par renforcement.
    """
    
    def __init__(self):
        self.q_table = {}  # Table Q simplifiée
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 0.1
    
    def generate_actions(
        self,
        policy_id: int,
        metrics: QoSMetrics,
        patterns: Dict[str, Any]
    ) -> List[OptimizationAction]:
        """
        Génère des actions basées sur l'apprentissage par renforcement.
        
        Args:
            policy_id: ID de la politique
            metrics: Métriques actuelles
            patterns: Patterns de trafic
            
        Returns:
            Liste d'actions d'optimisation
        """
        actions = []
        
        # État actuel (simplifié)
        state = self._encode_state(metrics, patterns)
        
        # Générer des actions candidates
        if metrics.latency > 50:  # Latence élevée
            actions.append(OptimizationAction(
                policy_id=policy_id,
                parameter_changes={'priority_adjustment': +1, 'buffer_size': -0.1},
                expected_improvement=0.15,
                confidence=0.8,
                strategy_used=OptimizationStrategy.REINFORCEMENT_LEARNING
            ))
        
        if metrics.packet_loss > 1.0:  # Perte de paquets élevée
            actions.append(OptimizationAction(
                policy_id=policy_id,
                parameter_changes={'queue_limit': +0.2, 'red_threshold': +0.1},
                expected_improvement=0.12,
                confidence=0.75,
                strategy_used=OptimizationStrategy.REINFORCEMENT_LEARNING
            ))
        
        if metrics.utilization > 80:  # Utilisation élevée
            actions.append(OptimizationAction(
                policy_id=policy_id,
                parameter_changes={'bandwidth_allocation': +0.1, 'burst_limit': -0.05},
                expected_improvement=0.10,
                confidence=0.7,
                strategy_used=OptimizationStrategy.REINFORCEMENT_LEARNING
            ))
        
        return actions
    
    def _encode_state(self, metrics: QoSMetrics, patterns: Dict[str, Any]) -> str:
        """
        Encode l'état actuel pour la table Q.
        
        Args:
            metrics: Métriques QoS
            patterns: Patterns de trafic
            
        Returns:
            État encodé
        """
        # Discrétiser les métriques
        latency_level = "high" if metrics.latency > 50 else "normal"
        loss_level = "high" if metrics.packet_loss > 1.0 else "normal"
        util_level = "high" if metrics.utilization > 80 else "normal"
        
        return f"{latency_level}_{loss_level}_{util_level}"
    
    def update_model(self, action: OptimizationAction, improvement: float):
        """
        Met à jour le modèle avec les résultats de l'action.
        
        Args:
            action: Action appliquée
            improvement: Amélioration observée
        """
        # Mise à jour simplifiée de la table Q
        state_key = f"policy_{action.policy_id}"
        action_key = str(action.parameter_changes)
        
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        
        if action_key not in self.q_table[state_key]:
            self.q_table[state_key][action_key] = 0.0
        
        # Mise à jour Q(s,a)
        reward = improvement * 100  # Convertir en récompense
        old_value = self.q_table[state_key][action_key]
        self.q_table[state_key][action_key] = old_value + self.learning_rate * (reward - old_value)


class GeneticAlgorithmOptimizer:
    """
    Optimiseur basé sur algorithme génétique.
    """
    
    def __init__(self):
        self.population_size = 20
        self.mutation_rate = 0.1
        self.generations = 10
    
    def generate_actions(
        self,
        policy_id: int,
        metrics: QoSMetrics,
        patterns: Dict[str, Any]
    ) -> List[OptimizationAction]:
        """
        Génère des actions en utilisant un algorithme génétique.
        
        Args:
            policy_id: ID de la politique
            metrics: Métriques actuelles
            patterns: Patterns de trafic
            
        Returns:
            Liste d'actions d'optimisation
        """
        actions = []
        
        # Générer population initiale de paramètres
        population = self._generate_initial_population()
        
        # Évoluer sur plusieurs générations
        for generation in range(self.generations):
            # Évaluer la fitness de chaque individu
            fitness_scores = [self._evaluate_fitness(individual, metrics) for individual in population]
            
            # Sélection et reproduction
            population = self._evolve_population(population, fitness_scores)
        
        # Sélectionner les meilleurs individus comme actions
        best_individuals = sorted(
            zip(population, [self._evaluate_fitness(ind, metrics) for ind in population]),
            key=lambda x: x[1],
            reverse=True
        )[:3]  # Top 3
        
        for individual, fitness in best_individuals:
            if fitness > 0.05:  # Seuil minimum
                actions.append(OptimizationAction(
                    policy_id=policy_id,
                    parameter_changes=individual,
                    expected_improvement=fitness,
                    confidence=0.6,
                    strategy_used=OptimizationStrategy.GENETIC_ALGORITHM
                ))
        
        return actions
    
    def _generate_initial_population(self) -> List[Dict[str, float]]:
        """Génère une population initiale de paramètres."""
        population = []
        
        for _ in range(self.population_size):
            individual = {
                'bandwidth_adjustment': np.random.uniform(-0.2, 0.2),
                'priority_adjustment': np.random.randint(-2, 3),
                'buffer_size_factor': np.random.uniform(0.8, 1.2),
                'queue_limit_factor': np.random.uniform(0.9, 1.1)
            }
            population.append(individual)
        
        return population
    
    def _evaluate_fitness(self, individual: Dict[str, float], metrics: QoSMetrics) -> float:
        """
        Évalue la fitness d'un individu.
        
        Args:
            individual: Paramètres à évaluer
            metrics: Métriques actuelles
            
        Returns:
            Score de fitness
        """
        # Simulation simplifiée de l'impact des paramètres
        fitness = 0.0
        
        # Récompenser la réduction de latence
        if individual['priority_adjustment'] > 0 and metrics.latency > 30:
            fitness += 0.1
        
        # Récompenser l'augmentation de bande passante si utilisation élevée
        if individual['bandwidth_adjustment'] > 0 and metrics.utilization > 80:
            fitness += 0.08
        
        # Pénaliser les changements extrêmes
        if abs(individual['bandwidth_adjustment']) > 0.15:
            fitness -= 0.05
        
        return max(0.0, fitness)
    
    def _evolve_population(
        self,
        population: List[Dict[str, float]],
        fitness_scores: List[float]
    ) -> List[Dict[str, float]]:
        """
        Fait évoluer la population vers la génération suivante.
        
        Args:
            population: Population actuelle
            fitness_scores: Scores de fitness
            
        Returns:
            Nouvelle population
        """
        new_population = []
        
        # Élitisme: garder les meilleurs
        elite_count = self.population_size // 4
        elite_indices = np.argsort(fitness_scores)[-elite_count:]
        for idx in elite_indices:
            new_population.append(population[idx].copy())
        
        # Compléter avec reproduction
        while len(new_population) < self.population_size:
            parent1, parent2 = self._select_parents(population, fitness_scores)
            child = self._crossover(parent1, parent2)
            child = self._mutate(child)
            new_population.append(child)
        
        return new_population
    
    def _select_parents(
        self,
        population: List[Dict[str, float]],
        fitness_scores: List[float]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Sélectionne deux parents pour la reproduction."""
        # Sélection par tournoi
        def tournament_select():
            tournament_size = 3
            candidates = np.random.choice(len(population), tournament_size, replace=False)
            best = max(candidates, key=lambda i: fitness_scores[i])
            return population[best]
        
        return tournament_select(), tournament_select()
    
    def _crossover(
        self,
        parent1: Dict[str, float],
        parent2: Dict[str, float]
    ) -> Dict[str, float]:
        """Crée un enfant par croisement de deux parents."""
        child = {}
        for key in parent1.keys():
            if np.random.random() < 0.5:
                child[key] = parent1[key]
            else:
                child[key] = parent2[key]
        return child
    
    def _mutate(self, individual: Dict[str, float]) -> Dict[str, float]:
        """Applique une mutation à un individu."""
        mutated = individual.copy()
        
        for key in mutated.keys():
            if np.random.random() < self.mutation_rate:
                if 'adjustment' in key:
                    mutated[key] += np.random.normal(0, 0.05)
                elif 'factor' in key:
                    mutated[key] *= np.random.uniform(0.95, 1.05)
        
        return mutated
    
    def update_model(self, action: OptimizationAction, improvement: float):
        """Met à jour le modèle génétique."""
        # Pour l'algorithme génétique, l'apprentissage se fait via l'évolution
        # Ici on pourrait ajuster les paramètres de l'algorithme
        if improvement > 0.1:
            self.mutation_rate = max(0.05, self.mutation_rate * 0.95)  # Réduire mutation
        else:
            self.mutation_rate = min(0.2, self.mutation_rate * 1.05)   # Augmenter mutation


class RuleBasedOptimizer:
    """
    Optimiseur basé sur des règles expertes.
    """
    
    def __init__(self):
        self.rules = self._load_optimization_rules()
    
    def generate_actions(
        self,
        policy_id: int,
        metrics: QoSMetrics,
        patterns: Dict[str, Any]
    ) -> List[OptimizationAction]:
        """
        Génère des actions basées sur des règles expertes.
        
        Args:
            policy_id: ID de la politique
            metrics: Métriques actuelles
            patterns: Patterns de trafic
            
        Returns:
            Liste d'actions d'optimisation
        """
        actions = []
        
        for rule in self.rules:
            if self._evaluate_rule_condition(rule, metrics, patterns):
                action = OptimizationAction(
                    policy_id=policy_id,
                    parameter_changes=rule['action'],
                    expected_improvement=rule['expected_improvement'],
                    confidence=rule['confidence'],
                    strategy_used=OptimizationStrategy.RULE_BASED
                )
                actions.append(action)
        
        return actions
    
    def _load_optimization_rules(self) -> List[Dict[str, Any]]:
        """Charge les règles d'optimisation expertes."""
        return [
            {
                'name': 'Réduire latence voix',
                'condition': lambda m, p: m.latency > 30 and 'voice' in p.get('dominant_applications', []),
                'action': {'voice_priority': +1, 'voice_buffer_size': -0.1},
                'expected_improvement': 0.15,
                'confidence': 0.9
            },
            {
                'name': 'Optimiser bande passante vidéo',
                'condition': lambda m, p: m.utilization > 85 and 'video_streaming' in p.get('dominant_applications', []),
                'action': {'video_bandwidth': +0.15, 'data_bandwidth': -0.1},
                'expected_improvement': 0.12,
                'confidence': 0.8
            },
            {
                'name': 'Réduire perte paquets',
                'condition': lambda m, p: m.packet_loss > 2.0,
                'action': {'global_queue_limit': +0.2, 'buffer_size': +0.15},
                'expected_improvement': 0.18,
                'confidence': 0.85
            },
            {
                'name': 'Optimiser jitter',
                'condition': lambda m, p: m.jitter > 20,
                'action': {'scheduling_algorithm': 'strict_priority', 'queue_weight': +0.1},
                'expected_improvement': 0.10,
                'confidence': 0.75
            }
        ]
    
    def _evaluate_rule_condition(
        self,
        rule: Dict[str, Any],
        metrics: QoSMetrics,
        patterns: Dict[str, Any]
    ) -> bool:
        """
        Évalue si une règle s'applique.
        
        Args:
            rule: Règle à évaluer
            metrics: Métriques actuelles
            patterns: Patterns de trafic
            
        Returns:
            True si la règle s'applique
        """
        try:
            return rule['condition'](metrics, patterns)
        except Exception:
            return False
    
    def update_model(self, action: OptimizationAction, improvement: float):
        """Met à jour le modèle basé sur règles."""
        # Pour les règles, on pourrait ajuster les seuils et confidences
        # basé sur les résultats historiques
        logger.info(f"Règle appliquée avec amélioration: {improvement:.2%}") 