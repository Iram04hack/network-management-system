#!/bin/bash

# Script d'initialisation réseau pour le framework de tests de sécurité
# À lancer avant core/real_security_framework.py

echo "🚀 Configuration de l'interface réseau pour les tests de sécurité..."

# Vérification des permissions sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être lancé avec sudo"
    exit 1
fi

# Affichage des interfaces actuelles
echo "📊 Interfaces réseau avant configuration:"
ip a

echo "🔧 Configuration de l'interface tap1..."
ifconfig tap1 10.255.255.1 netmask 255.255.255.0 up

echo "🔧 Configuration du routage NAT..."
iptables -t nat -A POSTROUTING -o wlp2s0 -j MASQUERADE

echo "🔧 Activation du forwarding IP..."
echo 1 > /proc/sys/net/ipv4/ip_forward

echo "📊 Interfaces réseau après configuration:"
ifconfig

echo "📊 Table de routage:"
ip route

echo "✅ Configuration réseau terminée avec succès!"
echo "🚀 Vous pouvez maintenant lancer le framework de tests"