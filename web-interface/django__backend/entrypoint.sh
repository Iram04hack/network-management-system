#!/bin/bash
set -e

# Attendre que PostgreSQL soit prêt
while ! nc -z ${POSTGRES_HOST:-postgres} 5432; do
  echo "En attente de PostgreSQL..."
  sleep 1
done

echo "PostgreSQL est prêt."

# Attendre que Redis soit prêt
while ! nc -z ${REDIS_HOST:-redis} 6379; do
  echo "En attente de Redis..."
  sleep 1
done

echo "Redis est prêt."

# Vérifier et installer les dépendances critiques manquantes
/app/check_dependencies.sh

# Appliquer les migrations
python manage.py migrate

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Créer un superutilisateur si nécessaire
python manage.py createsuperuser --noinput || echo "Le superutilisateur existe déjà."

# Si DJANGO_USE_SSL est true, utiliser HTTPS
if [ "${DJANGO_USE_SSL}" = "true" ]; then
  echo "Démarrage du serveur en mode HTTPS..."
  exec uvicorn nms_backend.asgi:application --host 0.0.0.0 --port 8000 --ssl-keyfile=/app/ssl/django.key --ssl-certfile=/app/ssl/django.crt
else
  echo "Démarrage du serveur en mode HTTP..."
  exec "$@"
fi
