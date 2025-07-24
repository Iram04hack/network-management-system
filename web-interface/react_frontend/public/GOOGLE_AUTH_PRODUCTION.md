# Configuration Google OAuth pour la Production

## 📋 Étapes de configuration

### 1. Créer un projet Google Cloud
1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un nouveau projet ou sélectionner un projet existant
3. Activer l'API Google+ et l'API Google OAuth2

### 2. Configurer OAuth 2.0
1. Dans la console Google Cloud, aller dans **APIs & Services > Credentials**
2. Cliquer sur **Create Credentials > OAuth 2.0 Client ID**
3. Choisir **Web application**
4. Ajouter les domaines autorisés :
   - **Authorized JavaScript origins** : `https://votre-domaine.com`
   - **Authorized redirect URIs** : `https://votre-domaine.com/login`

### 3. Variables d'environnement
Modifier le fichier `.env.production` :

```bash
# Remplacer par votre vrai Client ID
VITE_GOOGLE_CLIENT_ID=your-real-client-id.apps.googleusercontent.com

# URL de votre API backend
VITE_API_URL=https://api.votre-domaine.com

# Activer le mode production
VITE_ENVIRONMENT=production
```

### 4. Configuration backend requise
Votre backend doit implémenter l'endpoint `/api/auth/google/` pour valider les tokens JWT Google.

### 5. Sécurité
- ✅ Validation côté serveur des tokens Google
- ✅ Vérification de l'audience (client_id)
- ✅ Vérification de l'émetteur (Google)
- ✅ Vérification de l'expiration du token

## 🔧 Client ID de développement actuel
- **Client ID** : `678527770047-6cu06p1cc4p7r3goab147bul72tq2feh.apps.googleusercontent.com`
- **Domaines autorisés** : localhost, 127.0.0.1, 192.168.*

## ⚠️ Important
Ce Client ID de développement ne fonctionnera QUE en développement local. Pour la production, vous devez configurer votre propre projet Google Cloud.