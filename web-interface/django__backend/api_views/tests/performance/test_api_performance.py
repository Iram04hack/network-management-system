"""
Tests de performance pour le module API Views
Valide les performances des APIs avec filtrage, pagination et recherche avancée
"""

import time
import statistics
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import concurrent.futures
from threading import Thread


class APIPerformanceTestCase(APITestCase):
    """
    Classe de base pour les tests de performance des APIs
    """
    
    def setUp(self):
        """Configuration de base pour les tests de performance"""
        self.user = User.objects.create_user(
            username='perftest',
            email='perf@test.com',
            password='testpass123'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Métriques de performance
        self.max_response_time = 2.0  # 2 secondes max
        self.max_memory_usage = 100 * 1024 * 1024  # 100MB max
        self.min_throughput = 10  # 10 req/sec minimum
    
    def measure_response_time(self, url, method='GET', data=None, iterations=10):
        """
        Mesure le temps de réponse d'une API sur plusieurs itérations
        """
        response_times = []
        
        for _ in range(iterations):
            start_time = time.time()
            
            if method == 'GET':
                response = self.client.get(url)
            elif method == 'POST':
                response = self.client.post(url, data=data, format='json')
            elif method == 'PUT':
                response = self.client.put(url, data=data, format='json')
            elif method == 'DELETE':
                response = self.client.delete(url)
            
            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # Vérifier que la réponse est valide
            self.assertIn(response.status_code, [200, 201, 202, 204])
        
        return {
            'avg': statistics.mean(response_times),
            'min': min(response_times),
            'max': max(response_times),
            'median': statistics.median(response_times),
            'std_dev': statistics.stdev(response_times) if len(response_times) > 1 else 0
        }
    
    def measure_throughput(self, url, duration=10, concurrent_users=5):
        """
        Mesure le débit (throughput) d'une API
        """
        requests_completed = 0
        errors = 0
        start_time = time.time()
        
        def make_request():
            nonlocal requests_completed, errors
            try:
                response = self.client.get(url)
                if response.status_code == 200:
                    requests_completed += 1
                else:
                    errors += 1
            except Exception:
                errors += 1
        
        # Exécuter les requêtes en parallèle
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            while time.time() - start_time < duration:
                future = executor.submit(make_request)
                futures.append(future)
                time.sleep(0.1)  # Petit délai entre les requêtes
            
            # Attendre la fin de toutes les requêtes
            concurrent.futures.wait(futures)
        
        total_time = time.time() - start_time
        throughput = requests_completed / total_time
        
        return {
            'requests_completed': requests_completed,
            'errors': errors,
            'throughput': throughput,
            'error_rate': errors / (requests_completed + errors) if (requests_completed + errors) > 0 else 0
        }


class PaginationPerformanceTest(APIPerformanceTestCase):
    """
    Tests de performance pour la pagination
    """
    
    def test_pagination_standard_performance(self):
        """
        Test de performance de la pagination standard
        """
        # Test avec différentes tailles de page
        page_sizes = [10, 25, 50, 100]
        
        for page_size in page_sizes:
            with self.subTest(page_size=page_size):
                url = f'/api/v1/search/?page_size={page_size}&page=1'
                metrics = self.measure_response_time(url, iterations=5)
                
                # Vérifier que le temps de réponse est acceptable
                self.assertLessEqual(
                    metrics['avg'], 
                    self.max_response_time,
                    f"Pagination avec page_size={page_size} trop lente: {metrics['avg']:.3f}s"
                )
                
                # Plus la page est grande, plus le temps peut augmenter, mais pas linéairement
                if page_size <= 50:
                    self.assertLessEqual(metrics['avg'], 1.0)
    
    def test_cursor_pagination_performance(self):
        """
        Test de performance de la pagination cursor
        """
        url = '/api/v1/search/?pagination_type=cursor&page_size=25'
        metrics = self.measure_response_time(url, iterations=5)
        
        # La pagination cursor devrait être plus performante pour les gros datasets
        self.assertLessEqual(
            metrics['avg'], 
            1.0,  # Plus strict que la pagination standard
            f"Pagination cursor trop lente: {metrics['avg']:.3f}s"
        )
        
        # Vérifier la consistance des temps de réponse
        self.assertLessEqual(
            metrics['std_dev'],
            0.2,  # Écart-type faible = performance stable
            f"Performance de pagination cursor inconsistante: {metrics['std_dev']:.3f}s"
        )
    
    def test_large_offset_pagination_performance(self):
        """
        Test de performance avec des offsets importants
        """
        # Simuler une pagination profonde
        offsets = [0, 100, 500, 1000]
        
        baseline_time = None
        for offset in offsets:
            url = f'/api/v1/search/?limit=25&offset={offset}'
            metrics = self.measure_response_time(url, iterations=3)
            
            if baseline_time is None:
                baseline_time = metrics['avg']
            
            # Le temps ne devrait pas augmenter drastiquement avec l'offset
            performance_degradation = metrics['avg'] / baseline_time
            self.assertLessEqual(
                performance_degradation,
                3.0,  # Max 3x plus lent
                f"Dégradation de performance excessive à offset={offset}: {performance_degradation:.2f}x"
            )


class FilteringPerformanceTest(APIPerformanceTestCase):
    """
    Tests de performance pour le filtrage
    """
    
    def test_simple_filter_performance(self):
        """
        Test de performance des filtres simples
        """
        filters = [
            'device_type=router',
            'status=online',
            'vendor=Cisco'
        ]
        
        for filter_param in filters:
            with self.subTest(filter=filter_param):
                url = f'/api/v1/search/?{filter_param}'
                metrics = self.measure_response_time(url, iterations=5)
                
                self.assertLessEqual(
                    metrics['avg'],
                    self.max_response_time,
                    f"Filtre simple {filter_param} trop lent: {metrics['avg']:.3f}s"
                )
    
    def test_dynamic_filter_performance(self):
        """
        Test de performance des filtres dynamiques
        """
        dynamic_filters = [
            'filter[device_type][eq]=router',
            'filter[ip_address][contains]=192.168',
            'filter[created_at][gte]=2024-01-01',
            'filter[status][in]=online,maintenance'
        ]
        
        for filter_param in dynamic_filters:
            with self.subTest(filter=filter_param):
                url = f'/api/v1/search/?{filter_param}'
                metrics = self.measure_response_time(url, iterations=5)
                
                self.assertLessEqual(
                    metrics['avg'],
                    self.max_response_time,
                    f"Filtre dynamique {filter_param} trop lent: {metrics['avg']:.3f}s"
                )
    
    def test_multiple_filters_performance(self):
        """
        Test de performance avec plusieurs filtres combinés
        """
        url = '/api/v1/search/?device_type=router&filter[vendor][eq]=Cisco&filter[status][ne]=offline&page_size=25'
        metrics = self.measure_response_time(url, iterations=5)
        
        # Les filtres multiples devraient rester raisonnablement rapides
        self.assertLessEqual(
            metrics['avg'],
            self.max_response_time * 1.5,  # 50% de marge pour les filtres complexes
            f"Filtres multiples trop lents: {metrics['avg']:.3f}s"
        )


class SearchPerformanceTest(APIPerformanceTestCase):
    """
    Tests de performance pour la recherche
    """
    
    def test_global_search_performance(self):
        """
        Test de performance de la recherche globale
        """
        search_terms = ['router', 'cisco', '192.168', 'network']
        
        for term in search_terms:
            with self.subTest(term=term):
                url = f'/api/v1/search/?q={term}'
                metrics = self.measure_response_time(url, iterations=5)
                
                self.assertLessEqual(
                    metrics['avg'],
                    1.5,  # La recherche doit être rapide
                    f"Recherche pour '{term}' trop lente: {metrics['avg']:.3f}s"
                )
    
    def test_search_with_filters_performance(self):
        """
        Test de performance de la recherche avec filtres
        """
        url = '/api/v1/search/?q=router&resource_types=device&filter[vendor][eq]=Cisco'
        metrics = self.measure_response_time(url, iterations=5)
        
        self.assertLessEqual(
            metrics['avg'],
            2.0,
            f"Recherche avec filtres trop lente: {metrics['avg']:.3f}s"
        )
    
    def test_search_suggestions_performance(self):
        """
        Test de performance des suggestions de recherche
        """
        url = '/api/v1/search/suggestions/?q=rou'
        metrics = self.measure_response_time(url, iterations=10)
        
        # Les suggestions doivent être très rapides
        self.assertLessEqual(
            metrics['avg'],
            0.5,
            f"Suggestions de recherche trop lentes: {metrics['avg']:.3f}s"
        )


class ConcurrencyPerformanceTest(APIPerformanceTestCase):
    """
    Tests de performance en concurrence
    """
    
    def test_concurrent_dashboard_requests(self):
        """
        Test de performance avec requêtes concurrentes sur le dashboard
        """
        url = '/api/v1/dashboards/network/'
        metrics = self.measure_throughput(url, duration=10, concurrent_users=5)
        
        self.assertGreaterEqual(
            metrics['throughput'],
            self.min_throughput,
            f"Débit trop faible: {metrics['throughput']:.2f} req/s"
        )
        
        self.assertLessEqual(
            metrics['error_rate'],
            0.05,  # Max 5% d'erreurs
            f"Taux d'erreur trop élevé: {metrics['error_rate']:.2%}"
        )
    
    def test_concurrent_search_requests(self):
        """
        Test de performance avec recherches concurrentes
        """
        url = '/api/v1/search/?q=test'
        metrics = self.measure_throughput(url, duration=10, concurrent_users=3)
        
        # La recherche peut être moins performante que les vues simples
        self.assertGreaterEqual(
            metrics['throughput'],
            5,  # Au moins 5 req/s
            f"Débit de recherche trop faible: {metrics['throughput']:.2f} req/s"
        )
        
        self.assertLessEqual(
            metrics['error_rate'],
            0.1,  # Max 10% d'erreurs pour la recherche
            f"Taux d'erreur de recherche trop élevé: {metrics['error_rate']:.2%}"
        )


class MemoryPerformanceTest(APIPerformanceTestCase):
    """
    Tests de performance mémoire
    """
    
    def test_large_response_memory_usage(self):
        """
        Test d'usage mémoire avec de grandes réponses
        """
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Requête qui pourrait générer une grande réponse
        url = '/api/v1/search/?page_size=100'
        response = self.client.get(url)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        self.assertLessEqual(
            memory_increase,
            self.max_memory_usage,
            f"Augmentation mémoire excessive: {memory_increase / 1024 / 1024:.1f}MB"
        )
    
    def test_pagination_memory_efficiency(self):
        """
        Test d'efficacité mémoire de la pagination
        """
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Mesurer la mémoire pour différentes tailles de page
        memory_usage = {}
        
        for page_size in [10, 50, 100]:
            initial_memory = process.memory_info().rss
            
            url = f'/api/v1/search/?page_size={page_size}'
            response = self.client.get(url)
            
            final_memory = process.memory_info().rss
            memory_usage[page_size] = final_memory - initial_memory
        
        # La mémoire ne devrait pas augmenter de façon exponentielle
        # avec la taille de page
        memory_50 = memory_usage[50]
        memory_10 = memory_usage[10]
        
        if memory_10 > 0:
            ratio = memory_50 / memory_10
            self.assertLessEqual(
                ratio,
                10,  # Max 10x plus de mémoire pour 5x plus de données
                f"Usage mémoire non linéaire: ratio={ratio:.2f}"
            )


class StressTest(APIPerformanceTestCase):
    """
    Tests de stress pour valider la robustesse
    """
    
    def test_api_stress_test(self):
        """
        Test de stress sur les APIs principales
        """
        apis_to_test = [
            '/api/v1/dashboards/network/',
            '/api/v1/search/?q=test',
            '/api/v1/topology-discovery/',
        ]
        
        for api_url in apis_to_test:
            with self.subTest(api=api_url):
                # Test avec beaucoup de requêtes rapides
                metrics = self.measure_throughput(
                    api_url, 
                    duration=15, 
                    concurrent_users=10
                )
                
                # Vérifier que le système reste stable
                self.assertLessEqual(
                    metrics['error_rate'],
                    0.15,  # Max 15% d'erreurs en stress
                    f"API {api_url} instable sous stress: {metrics['error_rate']:.2%}"
                )
                
                self.assertGreaterEqual(
                    metrics['requests_completed'],
                    50,  # Au moins 50 requêtes réussies
                    f"API {api_url} pas assez performante: {metrics['requests_completed']} requêtes"
                )


class DatabasePerformanceTest(APIPerformanceTestCase):
    """
    Tests de performance des requêtes base de données
    """
    
    def test_n_plus_one_queries(self):
        """
        Test pour détecter les problèmes de requêtes N+1
        """
        from django.test.utils import override_settings
        from django.db import connection
        
        with override_settings(DEBUG=True):
            # Réinitialiser les requêtes
            connection.queries_log.clear()
            
            # Faire une requête qui pourrait avoir des problèmes N+1
            url = '/api/v1/search/?page_size=10'
            response = self.client.get(url)
            
            # Vérifier le nombre de requêtes DB
            num_queries = len(connection.queries)
            
            # Il ne devrait pas y avoir trop de requêtes
            self.assertLessEqual(
                num_queries,
                20,  # Max 20 requêtes pour une page de 10 éléments
                f"Trop de requêtes DB: {num_queries} (possible problème N+1)"
            )
    
    def test_query_optimization(self):
        """
        Test d'optimisation des requêtes avec select_related/prefetch_related
        """
        from django.test.utils import override_settings
        from django.db import connection
        
        with override_settings(DEBUG=True):
            connection.queries_log.clear()
            
            url = '/api/v1/search/?page_size=20&include_details=true'
            start_time = time.time()
            response = self.client.get(url)
            end_time = time.time()
            
            query_time = end_time - start_time
            num_queries = len(connection.queries)
            
            # Les requêtes optimisées devraient être rapides
            self.assertLessEqual(
                query_time,
                1.0,
                f"Requêtes avec détails trop lentes: {query_time:.3f}s"
            )
            
            # Et utiliser un nombre raisonnable de requêtes DB
            self.assertLessEqual(
                num_queries,
                10,
                f"Trop de requêtes DB même avec optimisation: {num_queries}"
            ) 