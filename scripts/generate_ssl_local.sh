#!/bin/bash

# Script pour générer des certificats SSL auto-signés pour Django sans sudo

# Obtenir le chemin du répertoire Django
DJANGO_DIR="/home/adjada/network-management-system/web-interface/django__backend"

# Répertoire de sortie pour les certificats (dans le projet Django)
CERT_DIR="$DJANGO_DIR/ssl"
CERT_FILE="$CERT_DIR/django.crt"
KEY_FILE="$CERT_DIR/django.key"

# Créer le répertoire si nécessaire
mkdir -p "$CERT_DIR"

# Vérifier si les certificats existent déjà
if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "✅ Certificats SSL déjà présents:"
    echo "   Certificat: $CERT_FILE"
    echo "   Clé privée: $KEY_FILE"
    exit 0
fi

# Générer les certificats SSL auto-signés
echo "🔐 Génération des certificats SSL auto-signés..."
openssl req -x509 -newkey rsa:4096 -keyout "$KEY_FILE" -out "$CERT_FILE" \
    -days 365 -nodes \
    -subj "/C=FR/ST=Paris/L=Paris/O=NMS/OU=Development/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:127.0.0.1,IP:127.0.0.1"

# Vérifier que les fichiers ont été créés
if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "✅ Certificats générés avec succès:"
    echo "   Certificat: $CERT_FILE"
    echo "   Clé privée: $KEY_FILE"
    
    # Définir les permissions appropriées
    chmod 644 "$CERT_FILE"
    chmod 600 "$KEY_FILE"
    
    echo "🔒 Permissions configurées correctement"
    exit 0
else
    echo "❌ Erreur lors de la génération des certificats"
    exit 1
fi