# Utiliser une image Python légère
FROM python:3.10-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt . 

# Copier les fichiers nécessaires
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update 
RUN apt-get install -y libgl1-mesa-dev
COPY requirements.txt .

# Copier le script Flask
COPY app.py .

# Commande par défaut pour démarrer l'application
CMD ["python", "app.py"]
