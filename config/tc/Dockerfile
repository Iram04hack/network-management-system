FROM python:3.10-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 \
    iptables \
    net-tools \
    ethtool \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer un utilisateur non-root
RUN useradd -m tcuser
RUN chown -R tcuser:tcuser /app

# Exposer le port
EXPOSE 5000

# Commande par défaut - ne peut pas s'exécuter en tant qu'utilisateur non-root en raison des opérations privilégiées
CMD ["python", "app.py"]
