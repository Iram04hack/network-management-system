/**
 * RealtimeDataSync.js - Service de synchronisation temps réel
 * Version d'urgence pour corriger la page blanche
 */

class RealtimeDataSync {
  constructor() {
    this.isRunning = false;
    this.modules = [];
    this.interval = null;
    this.intervalTime = 30000; // 30 secondes
    this.lastUpdate = null;
    this.errorCount = 0;
    
    console.log('[RealtimeDataSync] Service initialisé');
  }

  start(modules = []) {
    if (this.isRunning) {
      console.log('[RealtimeDataSync] Déjà en cours d\'exécution');
      return;
    }

    this.modules = modules;
    this.isRunning = true;
    this.errorCount = 0;
    
    console.log(`[RealtimeDataSync] Démarrage pour les modules: ${modules.join(', ')}`);
    
    // Simulation de synchronisation périodique
    this.interval = setInterval(() => {
      this.performSync();
    }, this.intervalTime);

    this.lastUpdate = new Date().toISOString();
  }

  stop() {
    if (!this.isRunning) {
      console.log('[RealtimeDataSync] Déjà arrêté');
      return;
    }

    this.isRunning = false;
    
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
    
    console.log('[RealtimeDataSync] Service arrêté');
  }

  performSync() {
    try {
      // Simulation de synchronisation
      console.log(`[RealtimeDataSync] Synchronisation des modules: ${this.modules.join(', ')}`);
      this.lastUpdate = new Date().toISOString();
      
      // Ici on pourrait déclencher des événements ou callbacks
      // Pour l'instant, c'est juste un placeholder
      
    } catch (error) {
      this.errorCount++;
      console.error('[RealtimeDataSync] Erreur lors de la synchronisation:', error);
      
      // Arrêter après trop d'erreurs
      if (this.errorCount > 5) {
        console.error('[RealtimeDataSync] Trop d\'erreurs, arrêt du service');
        this.stop();
      }
    }
  }

  getStatus() {
    return {
      running: this.isRunning,
      modules: this.modules,
      lastUpdate: this.lastUpdate,
      errorCount: this.errorCount,
      intervalTime: this.intervalTime
    };
  }

  getHealthStatus() {
    return {
      healthy: this.errorCount < 5,
      running: this.isRunning,
      lastUpdate: this.lastUpdate,
      errorCount: this.errorCount
    };
  }

  setInterval(time) {
    this.intervalTime = time;
    
    if (this.isRunning) {
      // Redémarrer avec le nouvel intervalle
      this.stop();
      this.start(this.modules);
    }
  }
}

const realtimeDataSync = new RealtimeDataSync();
export default realtimeDataSync;