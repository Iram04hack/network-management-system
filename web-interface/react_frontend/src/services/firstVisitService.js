class FirstVisitService {
  constructor() {
    this.FIRST_VISIT_KEY = 'nms_ever_visited';
    this.USER_FINGERPRINT_KEY = 'nms_user_fingerprint';
    this.VISIT_HISTORY_KEY = 'nms_visit_history';
  }

  // Générer une empreinte basée sur les caractéristiques du navigateur
  generateFingerprint() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('NMS Fingerprint', 2, 2);
    
    const fingerprint = {
      canvas: canvas.toDataURL(),
      screen: `${screen.width}x${screen.height}x${screen.colorDepth}`,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      language: navigator.language,
      platform: navigator.platform,
      userAgent: navigator.userAgent.substring(0, 100), // Tronqué pour éviter les changements
      cookieEnabled: navigator.cookieEnabled,
      timestamp: Date.now()
    };

    return btoa(JSON.stringify(fingerprint)).substring(0, 32);
  }

  // Vérifier si c'est vraiment la première visite
  isFirstVisit() {
    try {
      // 1. Vérifier le localStorage basique
      const hasVisited = localStorage.getItem(this.FIRST_VISIT_KEY);
      if (hasVisited) {
        return false;
      }

      // 2. Vérifier l'empreinte du navigateur
      const currentFingerprint = this.generateFingerprint();
      const storedFingerprint = localStorage.getItem(this.USER_FINGERPRINT_KEY);
      
      if (storedFingerprint === currentFingerprint) {
        return false;
      }

      // 3. Vérifier l'historique des visites
      const visitHistory = this.getVisitHistory();
      const today = new Date().toDateString();
      
      // Si on a déjà des visites aujourd'hui, ce n'est probablement pas la première fois
      if (visitHistory.some(visit => new Date(visit.date).toDateString() === today)) {
        return false;
      }

      // 4. Vérifier les cookies tiers (si supportés)
      if (this.checkThirdPartyCookie()) {
        return false;
      }

      return true;

    } catch (error) {
      console.error('Erreur lors de la vérification de première visite:', error);
      // En cas d'erreur, considérer comme première visite pour être sûr
      return true;
    }
  }

  // Marquer la visite actuelle
  markVisit(userType = 'anonymous') {
    try {
      const timestamp = new Date().toISOString();
      const fingerprint = this.generateFingerprint();
      
      // Marquer comme visité
      localStorage.setItem(this.FIRST_VISIT_KEY, timestamp);
      localStorage.setItem(this.USER_FINGERPRINT_KEY, fingerprint);
      
      // Ajouter à l'historique
      const visitHistory = this.getVisitHistory();
      visitHistory.push({
        date: timestamp,
        userType: userType,
        fingerprint: fingerprint.substring(0, 8) // Raccourci pour l'affichage
      });
      
      // Garder seulement les 30 dernières visites
      if (visitHistory.length > 30) {
        visitHistory.splice(0, visitHistory.length - 30);
      }
      
      localStorage.setItem(this.VISIT_HISTORY_KEY, JSON.stringify(visitHistory));
      
      // Essayer de définir un cookie tiers
      this.setThirdPartyCookie();
      
    } catch (error) {
      console.error('Erreur lors du marquage de visite:', error);
    }
  }

  // Obtenir l'historique des visites
  getVisitHistory() {
    try {
      const history = localStorage.getItem(this.VISIT_HISTORY_KEY);
      return history ? JSON.parse(history) : [];
    } catch (error) {
      console.error('Erreur lors de la lecture de l\'historique:', error);
      return [];
    }
  }

  // Obtenir le type d'utilisateur basé sur l'historique
  getUserType() {
    const history = this.getVisitHistory();
    const visitCount = history.length;
    
    if (visitCount === 0) {
      return 'first_time';
    } else if (visitCount < 3) {
      return 'returning';
    } else {
      return 'regular';
    }
  }

  // Obtenir le nombre de visites
  getVisitCount() {
    return this.getVisitHistory().length;
  }

  // Vérifier les cookies tiers (méthode basique)
  checkThirdPartyCookie() {
    try {
      const cookieName = 'nms_visit_marker';
      const cookies = document.cookie.split(';');
      
      return cookies.some(cookie => 
        cookie.trim().startsWith(`${cookieName}=`)
      );
    } catch (error) {
      return false;
    }
  }

  // Définir un cookie tiers
  setThirdPartyCookie() {
    try {
      const cookieName = 'nms_visit_marker';
      const cookieValue = Date.now();
      const expires = new Date();
      expires.setFullYear(expires.getFullYear() + 1); // 1 an
      
      document.cookie = `${cookieName}=${cookieValue}; expires=${expires.toUTCString()}; path=/; SameSite=Lax`;
    } catch (error) {
      console.log('Cookie non supporté:', error);
    }
  }

  // Obtenir les statistiques de visite
  getVisitStats() {
    const history = this.getVisitHistory();
    const now = new Date();
    
    const stats = {
      totalVisits: history.length,
      firstVisit: history.length > 0 ? history[0].date : null,
      lastVisit: history.length > 0 ? history[history.length - 1].date : null,
      visitsToday: history.filter(visit => 
        new Date(visit.date).toDateString() === now.toDateString()
      ).length,
      visitsThisWeek: history.filter(visit => {
        const visitDate = new Date(visit.date);
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        return visitDate > weekAgo;
      }).length
    };

    return stats;
  }

  // Nettoyer les données de visite (pour les tests)
  clearVisitData() {
    localStorage.removeItem(this.FIRST_VISIT_KEY);
    localStorage.removeItem(this.USER_FINGERPRINT_KEY);
    localStorage.removeItem(this.VISIT_HISTORY_KEY);
    
    // Nettoyer les cookies
    document.cookie = 'nms_visit_marker=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    
    console.log('🧹 Données de visite nettoyées');
  }

  // Méthode pour déboguer
  getDebugInfo() {
    return {
      fingerprint: this.generateFingerprint(),
      hasVisited: localStorage.getItem(this.FIRST_VISIT_KEY),
      visitHistory: this.getVisitHistory(),
      visitStats: this.getVisitStats(),
      userType: this.getUserType(),
      isFirstVisit: this.isFirstVisit()
    };
  }
}

export default new FirstVisitService();