"""
Widget de statistiques système pour le tableau de bord.

Ce widget affiche des statistiques système comme l'utilisation du CPU, 
de la mémoire et du disque.
"""
import os
import psutil
from datetime import datetime
from ..infrastructure.registry import register_plugin
from ...domain.interfaces import DashboardWidgetPlugin

@register_plugin('dashboard_widgets')
class SystemStatsWidget(DashboardWidgetPlugin):
    """Widget qui affiche des statistiques système en temps réel."""
    name = "system_stats"
    
    def initialize(self) -> bool:
        """Initialise le plugin."""
        try:
            # Vérifier que psutil est disponible
            psutil.cpu_percent()
            return True
        except Exception:
            return False
    
    def cleanup(self) -> bool:
        """Nettoie les ressources utilisées par le plugin."""
        return True
    
    def get_metadata(self):
        """Retourne les métadonnées du plugin."""
        return {
            'id': 'system_stats_widget',
            'name': 'Statistiques Système',
            'version': '1.0.0',
            'description': 'Affiche les statistiques systèmes en temps réel (CPU, mémoire, disque)',
            'author': 'Équipe NMS',
            'dependencies': [],
            'provides': ['dashboard_widget']
        }
    
    def get_widget_data(self, params=None):
        """
        Récupère les données du widget.
        
        Args:
            params: Paramètres optionnels pour customiser les données
            
        Returns:
            Dict contenant les données du widget
        """
        # Données CPU
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # Données mémoire
        memory = psutil.virtual_memory()
        
        # Données disque
        disk_usage = {}
        for part in psutil.disk_partitions(all=False):
            if os.name == 'nt':
                if 'cdrom' in part.opts or part.fstype == '':
                    continue
            usage = psutil.disk_usage(part.mountpoint)
            disk_usage[part.mountpoint] = {
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent
            }
        
        # Données réseau
        network = psutil.net_io_counters()
        
        # Temps d'activité
        boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
        uptime_seconds = (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds()
        
        # Formatter l'uptime en jours, heures, minutes, secondes
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{int(days)}j {int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        return {
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count,
                'current_freq': cpu_freq.current if cpu_freq else None,
                'min_freq': cpu_freq.min if cpu_freq and hasattr(cpu_freq, 'min') else None,
                'max_freq': cpu_freq.max if cpu_freq and hasattr(cpu_freq, 'max') else None
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            },
            'disk': disk_usage,
            'network': {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            },
            'system': {
                'boot_time': boot_time,
                'uptime': uptime
            },
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def render_widget(self, data=None):
        """
        Rend le widget en HTML.
        
        Args:
            data: Données à afficher (si None, get_widget_data sera appelée)
            
        Returns:
            HTML du widget
        """
        if data is None:
            data = self.get_widget_data()
        
        # Générer un rendu HTML simple du widget
        html = f"""
        <div class="system-stats-widget">
            <h3>Statistiques Système</h3>
            <div class="stat-section">
                <h4>CPU</h4>
                <div class="stat-item">
                    <span class="stat-label">Utilisation:</span> 
                    <span class="stat-value">{data['cpu']['percent']}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Cœurs:</span> 
                    <span class="stat-value">{data['cpu']['count']}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Fréquence:</span> 
                    <span class="stat-value">{data['cpu']['current_freq']} MHz</span>
                </div>
            </div>
            
            <div class="stat-section">
                <h4>Mémoire</h4>
                <div class="stat-item">
                    <span class="stat-label">Utilisation:</span> 
                    <span class="stat-value">{data['memory']['percent']}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Total:</span> 
                    <span class="stat-value">{data['memory']['total'] / (1024**3):.2f} GB</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Disponible:</span> 
                    <span class="stat-value">{data['memory']['available'] / (1024**3):.2f} GB</span>
                </div>
            </div>
            
            <div class="stat-section">
                <h4>Système</h4>
                <div class="stat-item">
                    <span class="stat-label">Temps d'activité:</span> 
                    <span class="stat-value">{data['system']['uptime']}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Démarré le:</span> 
                    <span class="stat-value">{data['system']['boot_time']}</span>
                </div>
            </div>
            
            <div class="stat-footer">
                Dernière mise à jour: {data['timestamp']}
            </div>
        </div>
        """
        
        return html 