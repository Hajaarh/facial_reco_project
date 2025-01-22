# README - Reconnaissance Faciale : Approche Docker

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

4. **RGPD-friendly** :  
   - Les photos uploadées ne sont pas stockées durablement : on calcule l’**embedding** (vecteur numérique) et on efface immédiatement l’image brute.  

---

## 3. Installation et Lancement

1. **Installer Docker** et **Docker Compose** (version >= 1.29).  
2. **Cloner** ce dépôt ou en télécharger l’archive :  
   ```bash
   git clone https://github.com/ton-projet/facial_recognition.git
   cd facial_recognition
