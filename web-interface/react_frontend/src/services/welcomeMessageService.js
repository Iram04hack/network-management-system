import sessionService from './sessionService';
import firstVisitService from './firstVisitService';

class WelcomeMessageService {
  constructor() {
    this.messages = {
      first_time: {
        morning: [
          "🌅 Bonjour ! Bienvenue dans votre nouvel espace de travail",
          "✨ Première connexion ! Votre tableau de bord est prêt",
          "🚀 Bienvenue ! Explorez toutes les fonctionnalités",
          "🎯 Bonjour ! Votre interface de gestion est opérationnelle",
          "💼 Première visite ? Parfait ! Commençons l'aventure"
        ],
        afternoon: [
          "☀️ Bon après-midi ! Découvrez votre nouvelle plateforme",
          "🛠️ Bienvenue ! Tous vos outils sont à portée de clic",
          "📊 Première connexion ! Votre dashboard vous attend",
          "⚡ Bienvenue dans l'univers de la gestion réseau",
          "🎨 Interface configurée ! Prêt à optimiser votre réseau ?"
        ],
        evening: [
          "🌆 Bonsoir ! Même en soirée, votre réseau reste surveillé",
          "🌙 Première soirée sur la plateforme ? Bienvenue !",
          "✨ Bonsoir ! Votre espace de monitoring est actif",
          "🔧 Soirée productive en perspective ? C'est parti !",
          "🌟 Bienvenue ! Votre réseau n'attend que vous"
        ],
        night: [
          "🌃 Bonsoir ! Les vrais pros travaillent la nuit",
          "🦉 Connexion nocturne ! Votre réseau veille avec vous",
          "⭐ Minuit passé ? Votre dedication impressionne !",
          "🌙 Bienvenue noctambule ! Tableau de bord prêt",
          "💻 Nuit blanche en perspective ? On vous accompagne"
        ]
      },
      returning: {
        morning: [
          "☕ Salut {name} ! Café et monitoring, parfait combo",
          "🌅 Re-bonjour {name} ! Prêt pour une nouvelle journée ?",
          "⚡ Hey {name} ! Votre réseau a bien dormi",
          "🎯 Bonjour {name} ! Quoi de neuf aujourd'hui ?",
          "💪 Salut {name} ! En forme pour optimiser ?",
          "🚀 Re-bonjour {name} ! On continue sur notre lancée ?"
        ],
        afternoon: [
          "🌞 Salut {name} ! L'après-midi parfait pour monitorer",
          "📈 Hey {name} ! Les métriques vous attendent",
          "⚡ Bon retour {name} ! Ready pour l'après-midi ?",
          "🎨 Salut {name} ! Votre réseau a de nouvelles données",
          "🔧 Re-bonjour {name} ! Temps d'optimiser encore ?",
          "💡 Hey {name} ! Des insights vous attendent"
        ],
        evening: [
          "🌆 Bonsoir {name} ! Soirée monitoring en vue ?",
          "⭐ Salut {name} ! Encore quelques ajustements ?",
          "🌙 Hey {name} ! Votre réseau vous a manqué ?",
          "💻 Bonsoir {name} ! Session productive en perspective",
          "🔥 Salut {name} ! Motivation du soir, espoir !",
          "✨ Re-bonsoir {name} ! Prêt à briller ?"
        ],
        night: [
          "🌃 Salut {name} ! Les nuits sont faites pour coder",
          "🦉 Hey {name} ! Noctambule du réseau en action",
          "⭐ Bonsoir {name} ! Minuit, l'heure des pros",
          "💻 Salut {name} ! Nuit blanche productive ?",
          "🌙 Hey {name} ! Votre réseau veille avec vous",
          "🔧 Re-bonsoir {name} ! Optimisation nocturne ?"
        ]
      },
      regular: {
        morning: [
          "☕ Morning {name} ! Routine matinale = check réseau",
          "⚡ Yo {name} ! Encore une journée de boss ?",
          "🎯 Salut expert ! {name}, le réseau t'attend",
          "🚀 Hey {name} ! Prêt à cartonner aujourd'hui ?",
          "💪 Salut chef ! {name}, en forme pour du monitoring ?",
          "🔥 Morning warrior {name} ! C'est parti !",
          "⭐ Salut pro ! {name}, quelles optimisations aujourd'hui ?"
        ],
        afternoon: [
          "🌞 Salut {name} ! Pause déj' finie, on reprend ?",
          "📊 Hey {name} ! L'après-midi des métriques",
          "⚡ Yo {name} ! Session boost en cours ?",
          "🎨 Salut artiste ! {name}, du beau monitoring en vue",
          "💡 Hey {name} ! Des idées géniales en tête ?",
          "🔧 Salut bricoleur ! {name}, on optimise quoi ?",
          "🚀 Afternoon power {name} ! Go go go !"
        ],
        evening: [
          "🌆 Bonsoir {name} ! Soirée geek au programme ?",
          "⭐ Salut {name} ! Encore motivé pour ce soir ?",
          "💻 Hey {name} ! Session marathon en approche ?",
          "🔥 Bonsoir boss ! {name}, ready pour du lourd ?",
          "🌙 Salut {name} ! La nuit porte conseil",
          "✨ Hey expert ! {name}, du monitoring de qualité ?",
          "⚡ Bonsoir {name} ! Productivité level max ?"
        ],
        night: [
          "🌃 Salut noctambule ! {name}, fidèle au poste",
          "🦉 Hey {name} ! Les vrais bossent la nuit",
          "⭐ Salut insomniaque ! {name}, ça monitoring dur",
          "💻 Bonsoir {name} ! Nuit blanche productive ?",
          "🌙 Hey champion ! {name}, toujours au top",
          "🔧 Salut perfectionniste ! {name}, jamais satisfait ?",
          "💡 Bonsoir génie ! {name}, inspiration nocturne ?"
        ]
      }
    };

    this.organizationMessages = [
      "🏢 Centre de contrôle {organization} - Tout sous votre regard",
      "🎯 Tableau de bord {organization} - Performance optimale",
      "⚡ Supervision {organization} - Votre expertise en action",
      "🚀 Centre névralgique {organization} - Innovation continue",
      "💡 Plateforme {organization} - Technologie sur mesure",
      "🔧 Interface dédiée {organization} - Efficacité maximale",
      "📊 Monitoring {organization} - Données en temps réel",
      "🛡️ Infrastructure {organization} - Sécurité renforcée",
      "⭐ Système {organization} - Excellence opérationnelle",
      "🌐 Réseau {organization} - Connectivité optimisée"
    ];

    this.interactiveElements = [
      "💡 Tip : Dernière visite il y a {timeSinceLastVisit} - Que du changement !",
      "📊 Stats : {visitCount} sessions - Vous êtes un habitué !",
      "🔔 Info : Session auto-prolongée - Travaillez sans interruption",
      "⚡ Perf : Système ultra-optimisé - Vitesse maximale !",
      "🛡️ Sécurité : Protection niveau entreprise - Dormez tranquille",
      "🌐 Status : Tous systèmes opérationnels - Green light partout !",
      "🎯 Workflow : Interface sur-mesure - Efficacité garantie",
      "📈 Live data : Monitoring temps réel - Rien ne vous échappe",
      "🔧 Setup : Config adaptée à vos besoins - Personnalisation max",
      "⏰ Smart session : Durée intelligente - Plus de déconnexions surprise",
      "🚀 Boost : Performance réseau au top - Vitesse de croisière",
      "💻 Pro mode : Interface avancée - Pour les experts comme vous",
      "🎨 UI/UX : Design optimisé - Plaisir visuel garanti",
      "🔥 Power user : {visitCount} connexions - Respect !",
      "⭐ Premium : Accès complet débloqué - Profitez de tout !"
    ];
  }

  // Obtenir un message de bienvenue personnalisé
  getWelcomeMessage() {
    const sessionData = sessionService.getSessionData();
    const timeOfDay = sessionService.getTimeOfDay();
    
    // Utiliser firstVisitService pour déterminer le type d'utilisateur
    const userType = firstVisitService.getUserType();
    const isFirstVisit = firstVisitService.isFirstVisit();
    
    // Si c'est vraiment la première visite
    if (isFirstVisit) {
      return this.getFirstTimeMessage(timeOfDay);
    }
    
    // Si on a des données de session (utilisateur connecté)
    if (sessionData && sessionData.user) {
      const userData = sessionData.user;
      const displayName = sessionService.getDisplayName(userData);
      const orgInfo = sessionService.getOrganizationInfo(userData);
      
      return this.getAuthenticatedMessage(userType, timeOfDay, displayName, orgInfo, sessionData);
    }
    
    // Utilisateur de retour mais pas connecté - utiliser first_time au lieu de returning
    return this.getFirstTimeMessage(timeOfDay);
  }

  // Obtenir un sous-titre contextuel
  getSubtitle(orgInfo) {
    if (orgInfo.hasOrganization) {
      const orgMessage = this.organizationMessages[Math.floor(Math.random() * this.organizationMessages.length)];
      return orgMessage.replace('{organization}', orgInfo.organizationName);
    }
    
    return "Votre solution complète de surveillance et gestion réseau";
  }

  // Obtenir un message interactif
  getInteractiveMessage(sessionData) {
    const randomInteractive = this.interactiveElements[Math.floor(Math.random() * this.interactiveElements.length)];
    const timeSinceLastVisit = this.calculateTimeSinceLastVisit(sessionData.loginTime);
    
    return randomInteractive
      .replace('{timeSinceLastVisit}', timeSinceLastVisit)
      .replace('{visitCount}', sessionData.visitCount || 1)
      .replace('{organization}', sessionData.user.company || 'votre organisation');
  }

  // Calculer le temps depuis la dernière visite
  calculateTimeSinceLastVisit(loginTime) {
    const now = new Date();
    const lastVisit = new Date(loginTime);
    const diffMs = now - lastVisit;
    
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffMinutes < 60) {
      return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''}`;
    } else if (diffHours < 24) {
      return `${diffHours} heure${diffHours > 1 ? 's' : ''}`;
    } else {
      return `${diffDays} jour${diffDays > 1 ? 's' : ''}`;
    }
  }

  // Message pour vraie première visite
  getFirstTimeMessage(timeOfDay) {
    const defaultMessages = this.messages.first_time[timeOfDay];
    
    return {
      main: defaultMessages[0],
      subtitle: null,
      interactive: null,
      userType: 'first_time',
      timeOfDay,
      displayName: null,
      organization: null
    };
  }

  // Message pour utilisateur connecté
  getAuthenticatedMessage(userType, timeOfDay, displayName, orgInfo, sessionData) {
    const messagePool = this.messages[userType][timeOfDay];
    const randomMessage = messagePool[Math.floor(Math.random() * messagePool.length)];
    
    const personalizedMessage = randomMessage
      .replace('{name}', displayName)
      .replace('{organization}', orgInfo.organizationName || 'votre organisation');

    return {
      main: personalizedMessage,
      subtitle: this.getSubtitle(orgInfo),
      interactive: this.getInteractiveMessage(sessionData),
      userType,
      timeOfDay,
      displayName,
      organization: orgInfo
    };
  }

  // Message par défaut (fallback)
  getDefaultMessage() {
    const timeOfDay = sessionService.getTimeOfDay();
    const defaultMessages = this.messages.first_time[timeOfDay];
    
    return {
      main: defaultMessages[0],
      subtitle: "Votre solution complète de surveillance et gestion réseau",
      interactive: "🔧 Chargement des préférences...",
      userType: 'first_time',
      timeOfDay,
      displayName: 'Utilisateur',
      organization: null
    };
  }

  // Obtenir un message de continuité (pour éviter la répétition)
  getContinuityMessage() {
    return {
      main: "De retour sur votre tableau de bord",
      subtitle: "Votre réseau n'a pas chômé en votre absence",
      interactive: "📈 Consultez les dernières métriques",
      type: 'continuity'
    };
  }
}

export default new WelcomeMessageService();