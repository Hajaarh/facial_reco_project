FROM python:3.10-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Installer les librairies système nécessaires à OpenCV/DeepFace
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application
COPY . .

# Commande par défaut pour démarrer l'application
CMD ["python", "app.py"]
