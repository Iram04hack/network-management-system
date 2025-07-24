"""
Package views du module dashboard.

Contient les vues Django et API REST pour l'interface du tableau de bord.
"""

from .dashboard_overview import DashboardOverviewView
from .network_overview import NetworkOverviewView
from .integrated_topology import IntegratedTopologyView
from .custom_dashboard import CustomDashboardView, DashboardStatsView

__all__ = [
    'DashboardOverviewView',
    'NetworkOverviewView',
    'IntegratedTopologyView',
    'CustomDashboardView',
    'DashboardStatsView'
] 