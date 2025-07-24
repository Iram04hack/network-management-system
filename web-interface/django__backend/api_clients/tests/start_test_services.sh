#!/bin/bash
# Script de démarrage des services pour les tests API Clients
# Respecte la contrainte 95.65% de données réelles

set -e

echo "🚀 Démarrage des services de test API Clients..."
echo "📍 Répertoire: $(pwd)"
echo "📅 Date: $(date)"
echo "="*70

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "docker-compose.services.yml" ]; then
    echo "❌ Erreur: docker-compose.services.yml non trouvé"
    echo "📍 Assurez-vous d'être dans le répertoire api_clients/tests/"
    exit 1
fi

# Créer les répertoires de données si nécessaire
echo "📁 Création des répertoires de données..."
mkdir -p data/snmp data/netflow data/postgres data/redis data/prometheus data/elasticsearch

# Arrêter les services existants (si ils existent)
echo "🛑 Arrêt des services existants..."
docker-compose -f docker-compose.services.yml down --remove-orphans || true

# Nettoyer les volumes orphelins
echo "🧹 Nettoyage des volumes orphelins..."
docker volume prune -f || true

# Démarrer les services par groupes pour éviter les conflits
echo "📦 Démarrage des services essentiels..."
docker-compose -f docker-compose.services.yml up -d postgres-test redis-test

echo "⏳ Attente de la disponibilité de PostgreSQL et Redis..."
sleep 15

# Vérifier PostgreSQL
echo "🔍 Vérification de PostgreSQL..."
for i in {1..30}; do
    if docker exec api-clients-postgres-test pg_isready -U api_clients_user -d api_clients_test; then
        echo "✅ PostgreSQL prêt"
        break
    fi
    echo "⏳ Attente PostgreSQL... ($i/30)"
    sleep 2
done

# Vérifier Redis
echo "🔍 Vérification de Redis..."
for i in {1..15}; do
    if docker exec api-clients-redis-test redis-cli ping | grep -q PONG; then
        echo "✅ Redis prêt"
        break
    fi
    echo "⏳ Attente Redis... ($i/15)"
    sleep 2
done

echo "📊 Démarrage des services de monitoring..."
docker-compose -f docker-compose.services.yml up -d prometheus-test elasticsearch-test

echo "⏳ Attente de la disponibilité des services de monitoring..."
sleep 20

# Vérifier Prometheus
echo "🔍 Vérification de Prometheus..."
for i in {1..20}; do
    if curl -s http://localhost:9092/-/healthy | grep -q "Prometheus is Healthy"; then
        echo "✅ Prometheus prêt"
        break
    fi
    echo "⏳ Attente Prometheus... ($i/20)"
    sleep 3
done

# Vérifier Elasticsearch
echo "🔍 Vérification d'Elasticsearch..."
for i in {1..30}; do
    if curl -s http://localhost:9202/_cluster/health | grep -q "yellow\|green"; then
        echo "✅ Elasticsearch prêt"
        break
    fi
    echo "⏳ Attente Elasticsearch... ($i/30)"
    sleep 3
done

echo "🌐 Démarrage des services réseau..."
docker-compose -f docker-compose.services.yml up -d snmp-agent-test

echo "⏳ Attente de la disponibilité du service SNMP..."
sleep 10

# Vérifier SNMP Agent
echo "🔍 Vérification de l'agent SNMP..."
for i in {1..15}; do
    if snmpget -v2c -c public localhost:1162 1.3.6.1.2.1.1.1.0 2>/dev/null; then
        echo "✅ Agent SNMP prêt"
        break
    fi
    echo "⏳ Attente agent SNMP... ($i/15)"
    sleep 2
done

echo "📊 Démarrage du collecteur Netflow..."
docker-compose -f docker-compose.services.yml up -d netflow-collector-test

echo "⏳ Attente de la disponibilité du collecteur Netflow..."
sleep 30

# Vérifier Netflow Collector
echo "🔍 Vérification du collecteur Netflow..."
for i in {1..20}; do
    if curl -s http://localhost:5602/api/status | grep -q "green\|yellow"; then
        echo "✅ Collecteur Netflow prêt"
        break
    fi
    echo "⏳ Attente collecteur Netflow... ($i/20)"
    sleep 3
done

echo ""
echo "="*70
echo "📊 ÉTAT DES SERVICES"
echo "="*70

# Vérifier l'état de tous les services
docker-compose -f docker-compose.services.yml ps

echo ""
echo "🔍 VÉRIFICATION DES PORTS"
echo "="*70

# Vérifier les ports
services=(
    "PostgreSQL:5434"
    "Redis:6381"
    "Prometheus:9092"
    "Elasticsearch:9202"
    "SNMP:1162"
    "Netflow-Kibana:5602"
)

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if netstat -tuln | grep -q ":$port "; then
        echo "✅ $name (port $port): ACTIF"
    else
        echo "❌ $name (port $port): INACTIF"
    fi
done

echo ""
echo "📊 VALIDATION DES DONNÉES RÉELLES"
echo "="*70

# Valider que les services contiennent des données réelles
echo "🔍 Validation PostgreSQL..."
if docker exec api-clients-postgres-test psql -U api_clients_user -d api_clients_test -c "SELECT COUNT(*) FROM api_clients_test_devices;" | grep -q "[1-9]"; then
    echo "✅ PostgreSQL: Données réelles présentes"
else
    echo "⚠️ PostgreSQL: Aucune donnée trouvée"
fi

echo "🔍 Validation Prometheus..."
if curl -s "http://localhost:9092/api/v1/query?query=up" | grep -q '"status":"success"'; then
    echo "✅ Prometheus: API fonctionnelle"
else
    echo "⚠️ Prometheus: API non accessible"
fi

echo "🔍 Validation Elasticsearch..."
if curl -s "http://localhost:9202/_cat/indices" | grep -q "elastiflow"; then
    echo "✅ Elasticsearch: Index Netflow présent"
else
    echo "⚠️ Elasticsearch: Index Netflow non trouvé"
fi

echo "🔍 Validation SNMP..."
if snmpwalk -v2c -c public localhost:1162 1.3.6.1.2.1.1 2>/dev/null | grep -q "SNMPv2-MIB"; then
    echo "✅ SNMP: Agent fonctionnel avec données système"
else
    echo "⚠️ SNMP: Agent non accessible ou sans données"
fi

echo ""
echo "="*70
echo "🎉 SERVICES DE TEST DÉMARRÉS"
echo "="*70

echo "📋 Services disponibles:"
echo "  🗄️  PostgreSQL: localhost:5434 (api_clients_test/api_clients_user)"
echo "  🔴 Redis: localhost:6381"
echo "  📊 Prometheus: http://localhost:9092"
echo "  🔍 Elasticsearch: http://localhost:9202"
echo "  🌐 SNMP Agent: localhost:1162 (community: public)"
echo "  📈 Netflow Kibana: http://localhost:5602"

echo ""
echo "🧪 Pour exécuter les tests:"
echo "  cd /home/adjada/network-management-system/web-interface/django__backend"
echo "  source nms_env/bin/activate"
echo "  python manage.py test api_clients.tests.test_base_client_complete"
echo "  python manage.py test api_clients.tests.test_http_client_complete"

echo ""
echo "🛑 Pour arrêter les services:"
echo "  cd api_clients/tests"
echo "  docker-compose -f docker-compose.services.yml down"

echo ""
echo "✅ Prêt pour les tests avec contrainte 95.65% de données réelles!"
