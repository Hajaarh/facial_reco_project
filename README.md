# Reconnaissance Faciale : Approche Docker

## 1. Contexte et Objectif

Ce projet implémente un **système de reconnaissance faciale** dont les fonctionnalités principales sont :
- **Enregistrer** un nouvel utilisateur (stockage des informations faciales sous forme d’“embeddings”).
- **Vérifier** l’identité d’un utilisateur (pointage) en comparant l’“embedding” de son visage à ceux présents dans la base de données.

Le tout est conçu pour être **exécuté via Docker**, offrant ainsi un déploiement simplifié :

1. **Installation automatique** des dépendances Python (Flask, DeepFace, etc.) à partir d’un fichier `requirements.txt`.
2. **Création automatique** de la base de données et des tables (grâce au code Flask qui invoque `db.create_all()`).
3. **Exposition** d’une interface web pour l’enregistrement et le pointage (via un simple front HTML/CSS/JS).

---

## 2. Architecture et Approche

### 2.1 Architecture globale

- **Docker Compose** orchestre plusieurs services :
  - **Service MySQL** (ou PostgreSQL) pour persister les embeddings et l’historique de pointage.
  - **Service Flask** pour l’API de reconnaissance (DeepFace, SQLAlchemy, etc.).

- **Fichier `requirements.txt`** : liste l’ensemble des dépendances Python (Flask, DeepFace, SQLAlchemy, etc.).  
  - Lors de la construction de l’image Docker pour le service Flask, un simple `pip install -r requirements.txt` installe tout le nécessaire.

- **Création automatique des tables** :  
  - Pas de script SQL manuel. Le code Flask appelle `db.create_all()` au démarrage, générant les tables (`employee`, `attendance_record`) dans la base MySQL.

### 2.2 Approche en détail

1. **Conteneur Flask**  
   - Basé sur Python 3.x + le contenu de `requirements.txt`.  
   - Contient le code de reconnaissance (appel à DeepFace) et d’expositions des routes `/register`, `/clock_in`, etc.  
   - Par défaut, écoute sur le port 5000.

2. **Conteneur MySQL**  
   - Géré via Docker Compose, avec les variables d’environnement (user, mot de passe, nom de la base) définies.  
   - Les tables sont créées automatiquement par l’ORM (SQLAlchemy) quand Flask démarre.

3. **Communication** :  
   - Les deux conteneurs partagent un **réseau Docker**.  
   - L’API Flask interagit avec MySQL via l’URI (ex. `mysql+pymysql://user:password@db:3306/facial_recognition`).  
   - L’interface HTML s’adresse à Flask sur `http://localhost:5000` (mappé par Docker).
   
---

## 3. Installation et Lancement

1. **Installer Docker** et **Docker Compose** (version >= 1.29).  
2. **Cloner** ce dépôt ou en télécharger l’archive :  
   ```bash
   git clone https://github.com/ton-projet/facial_recognition.git
   cd facial_recognition

3. Lancez Docker Compose pour construire et démarrer les conteneurs :
   ```bash
   sudo docker-compose up -d
   ```

4. Accédez à l’application via votre navigateur à l’adresse :
   - **Local** : `http://localhost:5000`
   - **Serveur AWS** : Remplacez `localhost` par l’adresse IP publique de votre instance EC2.

---
## 4. Configuration et Utilisation

### 4.1 Configuration des conteneurs
- **Base de données** :
  - MySQL est automatiquement initialisé avec les tables nécessaires (`Employee` et `AttendanceRecord`).
- **Fichier de dépendances** :
  - Le fichier `requirements.txt` contient toutes les bibliothèques nécessaires pour le backend Python.

### 4.2 Utilisation

1. **Enregistrer un nouvel utilisateur** :
   - Entrez le nom de l’utilisateur et téléchargez une photo via le formulaire prévu.
   - Le visage est traité pour générer un « embedding », ensuite sauvegardé dans la base.

2. **Pointage** :
   - Téléchargez une photo pour vérifier la correspondance avec les utilisateurs enregistrés.
   - Si une correspondance est trouvée (distance inférieure au seuil), le pointage est enregistré.

---


## 5. Déploiement sur AWS

1. **Configuration de l'instance EC2** :
   - Utilisez une instance avec Docker pré-installé (ex. : Amazon Linux ou Ubuntu).

2. **Accès SSH** :
   ```bash
   ssh -i "votre-cle.pem" ec2-user@votre-adresse-ip
   ```

3. **Lancer l'application** :
   - Clonez le dépôt sur l’instance, configurez Docker Compose, puis suivez les étapes d’installation.

4. **Sécurisation et accès distant** :
   - Configurez un groupe de sécurité AWS pour autoriser les connexions HTTP/HTTPS (ports 80 et 443).

---
## 7. Contributeur
- Hajar HAILAF
---




