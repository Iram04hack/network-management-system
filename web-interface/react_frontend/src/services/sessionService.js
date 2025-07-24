class SessionService {
  constructor() {
    this.SESSION_DURATION = 2 * 24 * 60 * 60 * 1000; // 2 jours
    this.EXTENDED_SESSION_DURATION = 3 * 24 * 60 * 60 * 1000; // 3 jours pour "Se souvenir de moi"
  }

  // Gérer les données de session
  setSessionData(userData, rememberMe = false) {
    const sessionData = {
      user: userData,
      loginTime: new Date().toISOString(),
      lastActivity: new Date().toISOString(),
      visitCount: this.getVisitCount() + 1,
      rememberMe: rememberMe,
      sessionExpiry: new Date(Date.now() + (rememberMe ? this.EXTENDED_SESSION_DURATION : this.SESSION_DURATION)).toISOString()
    };

    localStorage.setItem('session_data', JSON.stringify(sessionData));
    localStorage.setItem('last_visit', new Date().toISOString());
    
    return sessionData;
  }

  // Obtenir les données de session
  getSessionData() {
    try {
      const sessionData = localStorage.getItem('session_data');
      return sessionData ? JSON.parse(sessionData) : null;
    } catch (error) {
      console.error('Erreur lors de la lecture des données de session:', error);
      return null;
    }
  }

  // Vérifier si la session est valide
  isSessionValid() {
    const sessionData = this.getSessionData();
    if (!sessionData) return false;

    const now = new Date();
    const expiry = new Date(sessionData.sessionExpiry);
    
    return now < expiry;
  }

  // Mettre à jour l'activité
  updateActivity() {
    const sessionData = this.getSessionData();
    if (sessionData) {
      sessionData.lastActivity = new Date().toISOString();
      localStorage.setItem('session_data', JSON.stringify(sessionData));
    }
  }

  // Obtenir le nombre de visites
  getVisitCount() {
    const sessionData = this.getSessionData();
    return sessionData?.visitCount || 0;
  }

  // Obtenir le type d'utilisateur (première fois, retour, régulier)
  getUserType() {
    const visitCount = this.getVisitCount();
    const lastVisit = localStorage.getItem('last_visit');
    
    if (visitCount === 0 || !lastVisit) {
      return 'first_time';
    } else if (visitCount < 5) {
      return 'returning';
    } else {
      return 'regular';
    }
  }

  // Obtenir la période de la journée
  getTimeOfDay() {
    const hour = new Date().getHours();
    if (hour < 12) return 'morning';
    if (hour < 17) return 'afternoon';
    if (hour < 21) return 'evening';
    return 'night';
  }

  // Obtenir le nom d'affichage (gérer Google OAuth)
  getDisplayName(userData) {
    if (!userData) return 'Utilisateur';

    // Si c'est un utilisateur Google
    if (userData.provider === 'google' && userData.name) {
      // Prendre le prénom seulement
      return userData.name.split(' ')[0];
    }

    // Si c'est un utilisateur local avec prénom/nom
    if (userData.firstName) {
      return userData.firstName;
    }

    // Si on a un nom complet
    if (userData.name) {
      return userData.name.split(' ')[0];
    }

    // Fallback sur l'email
    if (userData.email) {
      return userData.email.split('@')[0];
    }

    return 'Utilisateur';
  }

  // Obtenir les informations d'organisation
  getOrganizationInfo(userData) {
    const orgInfo = {
      hasOrganization: false,
      organizationName: null,
      role: 'Utilisateur'
    };

    if (userData?.company) {
      orgInfo.hasOrganization = true;
      orgInfo.organizationName = userData.company;
    }

    if (userData?.role) {
      orgInfo.role = userData.role;
    } else if (userData?.email?.includes('admin')) {
      orgInfo.role = 'Administrateur';
    }

    return orgInfo;
  }

  // Nettoyer la session
  clearSession() {
    localStorage.removeItem('session_data');
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
  }

  // Prolonger la session
  extendSession() {
    const sessionData = this.getSessionData();
    if (sessionData) {
      const extension = sessionData.rememberMe ? this.EXTENDED_SESSION_DURATION : this.SESSION_DURATION;
      sessionData.sessionExpiry = new Date(Date.now() + extension).toISOString();
      sessionData.lastActivity = new Date().toISOString();
      localStorage.setItem('session_data', JSON.stringify(sessionData));
    }
  }
}

export default new SessionService();