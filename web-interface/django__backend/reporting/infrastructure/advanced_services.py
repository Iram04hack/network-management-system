"""
Services avancés d'infrastructure pour le module Reporting.

Ce module contient les implémentations des services avancés pour la visualisation,
l'analyse de données et l'intégration multi-sources.
"""

import logging
import json
import io
import os
import gzip
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, BinaryIO
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.utils import timezone
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

from ..domain.interfaces import (
    ReportStorageService,
    VisualizationService,
    AnalyticsService,
    DataIntegrationService,
    CacheService,
    ReportFormat,
    VisualizationType
)
from ..models import Report

logger = logging.getLogger(__name__)

class ReportStorageServiceImpl(ReportStorageService):
    """
    Implémentation du service de stockage des rapports.
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or getattr(settings, 'REPORTS_STORAGE_PATH', 'reports/')
        self.archive_path = os.path.join(self.storage_path, 'archive/')
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Assure que les répertoires existent."""
        os.makedirs(self.storage_path, exist_ok=True)
        os.makedirs(self.archive_path, exist_ok=True)
    
    def store(self, content: Any, report_type: str, file_format: str, 
              metadata: Optional[Dict[str, Any]] = None) -> str:
        """Stocke un rapport généré."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{report_type}_{timestamp}.{file_format}"
            file_path = os.path.join(self.storage_path, filename)
            
            # Stocker selon le type de contenu
            if isinstance(content, str):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            elif isinstance(content, bytes):
                with open(file_path, 'wb') as f:
                    f.write(content)
            elif isinstance(content, dict):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
            else:
                # Pour les DataFrames pandas ou autres objets
                if hasattr(content, 'to_csv') and file_format == 'csv':
                    content.to_csv(file_path, index=False)
                elif hasattr(content, 'to_excel') and file_format in ['xlsx', 'xls']:
                    content.to_excel(file_path, index=False)
                else:
                    raise ValueError(f"Format non supporté pour ce type de contenu: {type(content)}")
            
            # Stocker les métadonnées
            if metadata:
                metadata_path = file_path + '.meta'
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f)
            
            logger.info(f"Rapport stocké: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Erreur lors du stockage du rapport: {e}")
            raise
    
    def retrieve(self, file_path: str) -> Optional[BinaryIO]:
        """Récupère un rapport stocké."""
        try:
            if os.path.exists(file_path):
                return open(file_path, 'rb')
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du rapport {file_path}: {e}")
            return None
    
    def delete(self, file_path: str) -> bool:
        """Supprime un fichier de rapport."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                # Supprimer aussi les métadonnées si elles existent
                metadata_path = file_path + '.meta'
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                logger.info(f"Rapport supprimé: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du rapport {file_path}: {e}")
            return False
    
    def archive(self, file_path: str, archive_location: str = None) -> bool:
        """Archive un rapport ancien."""
        try:
            if not os.path.exists(file_path):
                return False
            
            # Utiliser l'emplacement d'archive par défaut si non spécifié
            if not archive_location:
                archive_location = self.archive_path
            
            # Créer le répertoire d'archive si nécessaire
            os.makedirs(archive_location, exist_ok=True)
            
            # Déplacer le fichier
            filename = os.path.basename(file_path)
            archive_path = os.path.join(archive_location, filename)
            shutil.move(file_path, archive_path)
            
            # Déplacer les métadonnées si elles existent
            metadata_path = file_path + '.meta'
            if os.path.exists(metadata_path):
                archive_meta_path = archive_path + '.meta'
                shutil.move(metadata_path, archive_meta_path)
            
            logger.info(f"Rapport archivé: {file_path} -> {archive_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'archivage du rapport {file_path}: {e}")
            return False
    
    def compress(self, file_path: str) -> str:
        """Compresse un fichier de rapport."""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Fichier non trouvé: {file_path}")
            
            compressed_path = file_path + '.gz'
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Supprimer le fichier original
            os.remove(file_path)
            
            logger.info(f"Rapport compressé: {file_path} -> {compressed_path}")
            return compressed_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la compression du rapport {file_path}: {e}")
            raise

class VisualizationServiceImpl(VisualizationService):
    """
    Implémentation du service de visualisation.
    """
    
    def create_visualization(self, data: Dict[str, Any], 
                           visualization_type: VisualizationType,
                           config: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une visualisation à partir des données."""
        try:
            if visualization_type == VisualizationType.CHART:
                return self._create_chart(data, config)
            elif visualization_type == VisualizationType.TABLE:
                return self._create_table(data, config)
            elif visualization_type == VisualizationType.GRAPH:
                return self._create_graph(data, config)
            elif visualization_type == VisualizationType.MAP:
                return self._create_map(data, config)
            elif visualization_type == VisualizationType.DASHBOARD:
                return self._create_dashboard(data, config)
            else:
                raise ValueError(f"Type de visualisation non supporté: {visualization_type}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de la visualisation: {e}")
            raise
    
    def _create_chart(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un graphique avec Plotly."""
        chart_type = config.get('chart_type', 'line')
        
        df = pd.DataFrame(data.get('values', []))
        
        if chart_type == 'line':
            fig = px.line(df, x=config.get('x_column'), y=config.get('y_column'),
                         title=config.get('title', 'Graphique en ligne'))
        elif chart_type == 'bar':
            fig = px.bar(df, x=config.get('x_column'), y=config.get('y_column'),
                        title=config.get('title', 'Graphique en barres'))
        elif chart_type == 'pie':
            fig = px.pie(df, values=config.get('values_column'), names=config.get('names_column'),
                        title=config.get('title', 'Graphique circulaire'))
        elif chart_type == 'scatter':
            fig = px.scatter(df, x=config.get('x_column'), y=config.get('y_column'),
                           title=config.get('title', 'Nuage de points'))
        else:
            raise ValueError(f"Type de graphique non supporté: {chart_type}")
        
        # Convertir en JSON pour l'intégration web
        graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)
        
        return {
            'type': 'chart',
            'chart_type': chart_type,
            'config': config,
            'plotly_json': graph_json,
            'created_at': datetime.now().isoformat()
        }
    
    def _create_table(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un tableau formaté."""
        df = pd.DataFrame(data.get('values', []))
        
        # Appliquer les configurations de formatage
        if 'column_formats' in config:
            for column, format_type in config['column_formats'].items():
                if column in df.columns:
                    if format_type == 'currency':
                        df[column] = df[column].apply(lambda x: f"€{x:,.2f}")
                    elif format_type == 'percentage':
                        df[column] = df[column].apply(lambda x: f"{x:.2%}")
        
        return {
            'type': 'table',
            'headers': list(df.columns),
            'rows': df.values.tolist(),
            'config': config,
            'created_at': datetime.now().isoformat()
        }
    
    def _create_graph(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un graphique réseau ou un diagramme."""
        # Implémentation pour les graphiques de réseau
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        
        return {
            'type': 'graph',
            'nodes': nodes,
            'edges': edges,
            'config': config,
            'created_at': datetime.now().isoformat()
        }
    
    def _create_map(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une carte géographique."""
        df = pd.DataFrame(data.get('values', []))
        
        fig = px.scatter_mapbox(
            df,
            lat=config.get('lat_column'),
            lon=config.get('lon_column'),
            hover_data=config.get('hover_columns', []),
            title=config.get('title', 'Carte'),
            mapbox_style='open-street-map'
        )
        
        graph_json = json.dumps(fig, cls=PlotlyJSONEncoder)
        
        return {
            'type': 'map',
            'plotly_json': graph_json,
            'config': config,
            'created_at': datetime.now().isoformat()
        }
    
    def _create_dashboard(self, data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un dashboard avec plusieurs widgets."""
        widgets = []
        
        for widget_config in config.get('widgets', []):
            widget_data = data.get(widget_config['data_key'], {})
            widget = self.create_visualization(
                widget_data,
                VisualizationType(widget_config['type']),
                widget_config
            )
            widgets.append(widget)
        
        return {
            'type': 'dashboard',
            'widgets': widgets,
            'layout': config.get('layout', {}),
            'created_at': datetime.now().isoformat()
        }
    
    def generate_interactive_dashboard(self, report_id: int,
                                     widgets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Génère un dashboard interactif."""
        try:
            report = Report.objects.get(pk=report_id)
            dashboard_config = {
                'report_id': report_id,
                'report_title': report.title,
                'widgets': widgets,
                'generated_at': datetime.now().isoformat()
            }
            
            # Générer les widgets
            dashboard_widgets = []
            for widget in widgets:
                widget_data = report.content.get(widget['data_source'], {})
                visualization = self.create_visualization(
                    widget_data,
                    VisualizationType(widget['type']),
                    widget['config']
                )
                dashboard_widgets.append(visualization)
            
            dashboard_config['widgets'] = dashboard_widgets
            
            return dashboard_config
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du dashboard pour le rapport {report_id}: {e}")
            raise
    
    def export_visualization(self, visualization_id: str, 
                           export_format: ReportFormat) -> str:
        """Exporte une visualisation dans un format spécifié."""
        # Implémentation pour l'export de visualisations
        # Cette méthode nécessiterait un système de stockage des visualisations
        raise NotImplementedError("Export de visualisations pas encore implémenté")

class AnalyticsServiceImpl(AnalyticsService):
    """
    Implémentation du service d'analyse avancée.
    """
    
    def detect_anomalies(self, data: List[Dict[str, Any]], 
                        config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Détecte les anomalies dans les données."""
        try:
            df = pd.DataFrame(data)
            
            # Configuration par défaut
            contamination = config.get('contamination', 0.1)
            features = config.get('features', [])
            
            if not features:
                # Utiliser toutes les colonnes numériques
                features = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if not features:
                return []
            
            # Préparer les données
            X = df[features].fillna(0)
            
            # Standardiser les données
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Détecter les anomalies avec Isolation Forest
            clf = IsolationForest(contamination=contamination, random_state=42)
            anomaly_labels = clf.fit_predict(X_scaled)
            
            # Identifier les anomalies
            anomalies = []
            for i, label in enumerate(anomaly_labels):
                if label == -1:  # Anomalie détectée
                    anomaly_score = clf.score_samples([X_scaled[i]])[0]
                    anomalies.append({
                        'index': i,
                        'data': data[i],
                        'anomaly_score': float(anomaly_score),
                        'features': {feature: float(X.iloc[i][feature]) for feature in features},
                        'detected_at': datetime.now().isoformat()
                    })
            
            logger.info(f"Détection d'anomalies terminée: {len(anomalies)} anomalies trouvées")
            return anomalies
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection d'anomalies: {e}")
            raise
    
    def predict_trends(self, historical_data: List[Dict[str, Any]], 
                      prediction_horizon: int) -> Dict[str, Any]:
        """Prédit les tendances futures."""
        try:
            df = pd.DataFrame(historical_data)
            
            # Convertir la colonne de date si elle existe
            date_column = None
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    df[col] = pd.to_datetime(df[col])
                    date_column = col
                    break
            
            if not date_column:
                raise ValueError("Aucune colonne de date trouvée dans les données")
            
            # Trier par date
            df = df.sort_values(date_column)
            
            # Prédire pour chaque colonne numérique
            predictions = {}
            for column in df.select_dtypes(include=[np.number]).columns:
                try:
                    # Préparer les données pour la régression
                    X = np.arange(len(df)).reshape(-1, 1)
                    y = df[column].values
                    
                    # Entraîner le modèle
                    model = LinearRegression()
                    model.fit(X, y)
                    
                    # Faire des prédictions
                    future_X = np.arange(len(df), len(df) + prediction_horizon).reshape(-1, 1)
                    future_y = model.predict(future_X)
                    
                    # Calculer la confiance (R²)
                    confidence = model.score(X, y)
                    
                    predictions[column] = {
                        'values': future_y.tolist(),
                        'confidence': float(confidence),
                        'trend': 'increasing' if model.coef_[0] > 0 else 'decreasing',
                        'slope': float(model.coef_[0])
                    }
                    
                except Exception as e:
                    logger.warning(f"Impossible de prédire pour la colonne {column}: {e}")
            
            return {
                'predictions': predictions,
                'horizon_days': prediction_horizon,
                'generated_at': datetime.now().isoformat(),
                'data_points_used': len(df)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction de tendances: {e}")
            raise
    
    def generate_insights(self, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère des insights automatiques."""
        insights = []
        
        try:
            # Analyser les données pour générer des insights
            if 'values' in report_data and isinstance(report_data['values'], list):
                df = pd.DataFrame(report_data['values'])
                
                # Insights statistiques de base
                for column in df.select_dtypes(include=[np.number]).columns:
                    data = df[column].dropna()
                    if len(data) > 0:
                        mean_val = data.mean()
                        std_val = data.std()
                        
                        # Insight sur la variabilité
                        if std_val > 0:
                            cv = std_val / mean_val if mean_val != 0 else float('inf')
                            if cv > 0.5:
                                insights.append({
                                    'type': 'variability',
                                    'column': column,
                                    'message': f"La colonne '{column}' présente une forte variabilité (CV: {cv:.2f})",
                                    'severity': 'medium',
                                    'value': float(cv)
                                })
                        
                        # Insight sur les valeurs extrêmes
                        q1 = data.quantile(0.25)
                        q3 = data.quantile(0.75)
                        iqr = q3 - q1
                        outliers = data[(data < q1 - 1.5 * iqr) | (data > q3 + 1.5 * iqr)]
                        
                        if len(outliers) > 0:
                            insights.append({
                                'type': 'outliers',
                                'column': column,
                                'message': f"{len(outliers)} valeurs aberrantes détectées dans '{column}'",
                                'severity': 'high' if len(outliers) > len(data) * 0.1 else 'low',
                                'count': len(outliers)
                            })
            
            logger.info(f"Génération d'insights terminée: {len(insights)} insights générés")
            return insights
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'insights: {e}")
            return insights
    
    def correlation_analysis(self, datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyse les corrélations entre différents datasets."""
        try:
            # Combiner tous les datasets
            combined_df = pd.DataFrame()
            
            for i, dataset in enumerate(datasets):
                if 'values' in dataset and isinstance(dataset['values'], list):
                    df = pd.DataFrame(dataset['values'])
                    # Préfixer les colonnes avec l'index du dataset
                    df.columns = [f"ds{i}_{col}" for col in df.columns]
                    if combined_df.empty:
                        combined_df = df
                    else:
                        combined_df = pd.concat([combined_df, df], axis=1)
            
            # Calculer la matrice de corrélation
            numeric_cols = combined_df.select_dtypes(include=[np.number]).columns
            correlation_matrix = combined_df[numeric_cols].corr()
            
            # Identifier les corrélations significatives
            significant_correlations = []
            threshold = 0.7  # Seuil de corrélation significative
            
            for i in range(len(correlation_matrix.columns)):
                for j in range(i + 1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) > threshold:
                        significant_correlations.append({
                            'variable1': correlation_matrix.columns[i],
                            'variable2': correlation_matrix.columns[j],
                            'correlation': float(corr_value),
                            'strength': 'strong' if abs(corr_value) > 0.8 else 'moderate'
                        })
            
            return {
                'correlation_matrix': correlation_matrix.to_dict(),
                'significant_correlations': significant_correlations,
                'analysis_date': datetime.now().isoformat(),
                'datasets_analyzed': len(datasets)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de corrélation: {e}")
            raise

class DataIntegrationServiceImpl(DataIntegrationService):
    """
    Implémentation du service d'intégration de données.
    """
    
    def integrate_data_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Intègre des données de sources multiples."""
        try:
            integrated_data = {}
            metadata = {
                'sources_count': len(sources),
                'integration_date': datetime.now().isoformat(),
                'source_details': []
            }
            
            for i, source in enumerate(sources):
                source_type = source.get('type')
                source_data = source.get('data', {})
                
                # Traiter selon le type de source
                if source_type == 'database':
                    processed_data = self._integrate_database_source(source)
                elif source_type == 'api':
                    processed_data = self._integrate_api_source(source)
                elif source_type == 'file':
                    processed_data = self._integrate_file_source(source)
                elif source_type == 'direct':
                    processed_data = source_data
                else:
                    logger.warning(f"Type de source non supporté: {source_type}")
                    continue
                
                # Ajouter les données intégrées
                source_key = source.get('name', f'source_{i}')
                integrated_data[source_key] = processed_data
                
                # Ajouter les métadonnées
                metadata['source_details'].append({
                    'name': source_key,
                    'type': source_type,
                    'records_count': len(processed_data) if isinstance(processed_data, list) else 1,
                    'integration_status': 'success'
                })
            
            return {
                'data': integrated_data,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration des données: {e}")
            raise
    
    def _integrate_database_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Intègre une source de données de base de données."""
        # Implémentation pour l'intégration de base de données
        # Cette méthode nécessiterait des connecteurs spécifiques
        logger.info("Intégration de source de base de données")
        return source.get('data', [])
    
    def _integrate_api_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Intègre une source de données API."""
        # Implémentation pour l'intégration d'API
        # Cette méthode nécessiterait des appels HTTP
        logger.info("Intégration de source API")
        return source.get('data', [])
    
    def _integrate_file_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Intègre une source de données de fichier."""
        # Implémentation pour l'intégration de fichiers
        logger.info("Intégration de source de fichier")
        return source.get('data', [])
    
    def transform_data(self, data: Dict[str, Any], 
                      transformation_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transforme les données selon des règles définies."""
        try:
            transformed_data = data.copy()
            
            for rule in transformation_rules:
                rule_type = rule.get('type')
                target_field = rule.get('target_field')
                
                if rule_type == 'rename':
                    # Renommer un champ
                    old_name = rule.get('old_name')
                    new_name = rule.get('new_name')
                    if old_name in transformed_data and new_name:
                        transformed_data[new_name] = transformed_data.pop(old_name)
                
                elif rule_type == 'calculate':
                    # Calculer un nouveau champ
                    expression = rule.get('expression')
                    if target_field and expression:
                        # Évaluation sécurisée d'expressions simples
                        try:
                            # Pour une implémentation complète, utiliser un parseur d'expressions sécurisé
                            transformed_data[target_field] = eval(expression, {"__builtins__": {}}, transformed_data)
                        except Exception as e:
                            logger.warning(f"Impossible d'évaluer l'expression {expression}: {e}")
                
                elif rule_type == 'filter':
                    # Filtrer les données
                    condition = rule.get('condition')
                    if condition and isinstance(transformed_data.get('values'), list):
                        # Implémentation simple de filtrage
                        filtered_values = []
                        for item in transformed_data['values']:
                            # Évaluation sécurisée de la condition
                            try:
                                if eval(condition, {"__builtins__": {}}, item):
                                    filtered_values.append(item)
                            except Exception:
                                pass  # Ignorer les erreurs de condition
                        transformed_data['values'] = filtered_values
                
                elif rule_type == 'aggregate':
                    # Agréger les données
                    if isinstance(transformed_data.get('values'), list):
                        df = pd.DataFrame(transformed_data['values'])
                        group_by = rule.get('group_by', [])
                        aggregations = rule.get('aggregations', {})
                        
                        if group_by and aggregations:
                            grouped = df.groupby(group_by).agg(aggregations).reset_index()
                            transformed_data['values'] = grouped.to_dict('records')
            
            return transformed_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la transformation des données: {e}")
            raise
    
    def validate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valide la qualité des données."""
        try:
            quality_report = {
                'validation_date': datetime.now().isoformat(),
                'overall_score': 0.0,
                'issues': [],
                'metrics': {}
            }
            
            if 'values' in data and isinstance(data['values'], list):
                df = pd.DataFrame(data['values'])
                total_cells = df.size
                
                # Vérifier les valeurs manquantes
                missing_count = df.isnull().sum().sum()
                missing_percentage = (missing_count / total_cells) * 100 if total_cells > 0 else 0
                
                quality_report['metrics']['missing_values_percentage'] = missing_percentage
                
                if missing_percentage > 10:
                    quality_report['issues'].append({
                        'type': 'missing_values',
                        'severity': 'high' if missing_percentage > 30 else 'medium',
                        'message': f"{missing_percentage:.1f}% de valeurs manquantes détectées",
                        'percentage': missing_percentage
                    })
                
                # Vérifier les duplicatas
                if len(df) > 0:
                    duplicates_count = df.duplicated().sum()
                    duplicates_percentage = (duplicates_count / len(df)) * 100
                    
                    quality_report['metrics']['duplicates_percentage'] = duplicates_percentage
                    
                    if duplicates_percentage > 5:
                        quality_report['issues'].append({
                            'type': 'duplicates',
                            'severity': 'medium',
                            'message': f"{duplicates_percentage:.1f}% de lignes dupliquées détectées",
                            'count': duplicates_count
                        })
                
                # Calculer le score global de qualité
                base_score = 100.0
                base_score -= missing_percentage * 0.5  # Pénalité pour valeurs manquantes
                base_score -= duplicates_percentage * 0.3  # Pénalité pour duplicatas
                
                quality_report['overall_score'] = max(0.0, base_score)
            
            return quality_report
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation de qualité des données: {e}")
            raise

class CacheServiceImpl(CacheService):
    """
    Implémentation du service de cache utilisant Django Cache.
    """
    
    def __init__(self, cache_prefix: str = 'reporting'):
        self.cache_prefix = cache_prefix
    
    def _make_key(self, key: str) -> str:
        """Créé une clé de cache avec préfixe."""
        return f"{self.cache_prefix}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache."""
        try:
            cache_key = self._make_key(key)
            return cache.get(cache_key)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du cache {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Met en cache une valeur."""
        try:
            cache_key = self._make_key(key)
            timeout = ttl or getattr(settings, 'REPORTING_CACHE_TTL', 3600)  # 1 heure par défaut
            cache.set(cache_key, value, timeout)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise en cache {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Supprime une entrée du cache."""
        try:
            cache_key = self._make_key(key)
            cache.delete(cache_key)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du cache {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalide toutes les clés correspondant à un pattern."""
        try:
            # Django cache ne supporte pas nativement l'invalidation par pattern
            # Cette implémentation dépend du backend de cache utilisé
            # Pour Redis, on pourrait utiliser redis-py directement
            logger.warning("Invalidation par pattern non implémentée pour ce backend de cache")
            return 0
        except Exception as e:
            logger.error(f"Erreur lors de l'invalidation du pattern {pattern}: {e}")
            return 0 