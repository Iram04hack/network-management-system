FROM python:3.10-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    curl \
    procps \
    nmap \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances principales en premier
RUN pip --default-timeout=1000 install --no-cache-dir dependency_injector>=4.41.0 aiohttp

# Installer les dépendances critiques pour éviter les erreurs de démarrage
RUN pip --default-timeout=1000 install --no-cache-dir \
    django-sslserver \
    plotly \
    seaborn \
    elasticsearch \
    matplotlib \
    pandas \
    numpy

# Installer les autres dépendances Python
RUN pip --default-timeout=1000 install --no-cache-dir -r requirements.txt && \
    pip --default-timeout=1000 install --no-cache-dir python-nmap whitenoise

# Copier le code source
COPY . .

# Créer les répertoires pour les certificats SSL
RUN mkdir -p /app/ssl

# Rendre les scripts exécutables
RUN chmod +x entrypoint.sh check_dependencies.sh

# Exposer le port
EXPOSE 8000

# Point d'entrée
ENTRYPOINT ["/app/entrypoint.sh"]

# Commande par défaut (sans SSL - sera écrasée par la configuration dans docker-compose.yml)
CMD ["uvicorn", "nms_backend.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
