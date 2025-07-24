#!/bin/bash

# Script pour générer des certificats SSL auto-signés pour le développement

# Répertoire de sortie pour les certificats
CERT_DIR="/etc/ssl/certs"
KEY_DIR="/etc/ssl/private"

# Créer les répertoires si nécessaire
sudo mkdir -p $CERT_DIR
sudo mkdir -p $KEY_DIR

# Générer une clé privée
echo "Génération de la clé privée..."
sudo openssl genrsa -out $KEY_DIR/nms-key.pem 2048

# Générer un certificat auto-signé
echo "Génération du certificat auto-signé..."
sudo openssl req -x509 -new -nodes -key $KEY_DIR/nms-key.pem \
    -sha256 -days 365 -out $CERT_DIR/nms-cert.pem \
    -subj "/C=FR/ST=Paris/L=Paris/O=NMS/OU=Development/CN=localhost"

# Vérifier que les fichiers ont été créés
if [ -f "$CERT_DIR/nms-cert.pem" ] && [ -f "$KEY_DIR/nms-key.pem" ]; then
    echo "Certificats générés avec succès:"
    echo "Certificat: $CERT_DIR/nms-cert.pem"
    echo "Clé privée: $KEY_DIR/nms-key.pem"
    
    # Définir les permissions appropriées
    sudo chmod 644 $CERT_DIR/nms-cert.pem
    sudo chmod 600 $KEY_DIR/nms-key.pem
else
    echo "Erreur lors de la génération des certificats."
    exit 1
fi

echo "Vous pouvez maintenant configurer Nginx pour utiliser ces certificats."
echo "IMPORTANT: Ce certificat est auto-signé et destiné uniquement au développement." 