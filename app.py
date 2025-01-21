from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
import json
import numpy as np
from datetime import datetime

# ----- DeepFace pour la reconnaissance faciale -----
from deepface import DeepFace

app = Flask(__name__)

# ----------------------------------------------------
# Configuration MySQL (adaptée à Docker Compose)
# ----------------------------------------------------

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://user:password@db:3306/facial_recognition"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ----------------------------------------------------
# Modèle Employee : on stocke le nom et l'embedding
# ----------------------------------------------------
class Employee(db.Model):
    __tablename__ = 'employee'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    embedding = db.Column(db.Text, nullable=False)  # On stocke un embedding sous forme JSON

# ----------------------------------------------------
# Modèle AttendanceRecord : on stocke l'heure de pointage
# ----------------------------------------------------
class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_record'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', backref='attendance_records')

# ----------------------------------------------------
# Utilitaire : extraire un embedding facial via DeepFace
# ----------------------------------------------------
def get_face_embedding(image_path):
    """
    Utilise DeepFace avec le modèle FaceNet pour obtenir un embedding (vecteur numérique).
    Retourne une liste Python (par ex. 128 valeurs).
    """
    # DeepFace.represent -> renvoie une liste de floats représentant le visage
    embedding_vector = DeepFace.represent(
        img_path=image_path,
        model_name="Facenet",          
        detector_backend="mtcnn"        # pour détection du visage (ou 'opencv', 'retinaface', etc.)
    )
    return embedding_vector

# ----------------------------------------------------
# Page d'accueil avec deux formulaires :
#  - Pour enregistrer un nouvel employé ("register")
#  - Pour faire le pointage ("clock_in")
# ----------------------------------------------------
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


# ----------------------------------------------------
# Route pour enregistrer un nouvel employé
# ----------------------------------------------------
@app.route('/register', methods=['POST'])
def register_employee():
    """
    Attend un formulaire contenant 'name' et 'image' :
      - name : nom de la personne
      - image : fichier image (jpg, png...)
    On calcule son embedding, puis on l'ajoute à la base.
    """
    name = request.form.get("name")
    if "image" not in request.files or not name:
        return jsonify({"error": "Missing 'name' or 'image' in the form-data."}), 400

    image_file = request.files["image"]

    # On sauvegarde temporairement l'image
    temp_path = f"temp_{uuid.uuid4()}.jpg"
    image_file.save(temp_path)

    try:
        # Obtenir l'embedding
        embedding = get_face_embedding(temp_path)  # liste de floats
    except Exception as e:
        os.remove(temp_path)
        return jsonify({"error": str(e)}), 500
    finally:
        # On supprime l'image brute (pas de stockage long terme)
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Convertir l'embedding en JSON pour stocker en BDD
    embedding_json = json.dumps(embedding)

    # Créer un nouvel employé
    new_emp = Employee(name=name, embedding=embedding_json)
    db.session.add(new_emp)
    try:
        db.session.commit()
    except Exception as e:
        
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": f"Employee '{name}' registered successfully."})


# ----------------------------------------------------
# Route pour faire le pointage (clock_in)
# ----------------------------------------------------
@app.route('/clock_in', methods=['POST'])
def clock_in():
    """
    Attend un fichier 'image' :
      - On calcule l'embedding
      - On compare avec tous ceux en base
      - On trouve le plus proche. Si distance < threshold => pointage validé
    """
    if "image" not in request.files:
        return jsonify({"error": "No image provided."}), 400

    image_file = request.files["image"]
    temp_path = f"temp_{uuid.uuid4()}.jpg"
    image_file.save(temp_path)

    try:
        unknown_emb = get_face_embedding(temp_path)
    except Exception as e:
        os.remove(temp_path)
        return jsonify({"error": str(e)}), 500
    finally:
        # On supprime l'image brute après usage
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Charger la liste de tous les employés
    employees = Employee.query.all()

    # Convertir l'unknown_emb en array pour manip plus aisée
    unknown_emb_array = np.array(unknown_emb)

    best_match = None
    best_distance = float("inf")

    # Seuil empirique pour FaceNet (ex. 10.0)
    # À ajuster selon le modèle ("Facenet", "Facenet512", etc.)
    threshold = 10.0

    for emp in employees:
        emp_emb_array = np.array(json.loads(emp.embedding))  # reconvertir la string JSON en liste, puis en array
        dist = np.linalg.norm(unknown_emb_array - emp_emb_array)
        if dist < best_distance:
            best_distance = dist
            best_match = emp

    if best_match and best_distance < threshold:
        # On enregistre le pointage
        record = AttendanceRecord(employee_id=best_match.id)
        db.session.add(record)
        db.session.commit()
        return jsonify({
            "message": f"Attendance recorded for {best_match.name}.",
            "distance": best_distance
        })
    else:
        return jsonify({"error": "No matching face found.", "distance": best_distance}), 404


# ----------------------------------------------------
# Main
# ----------------------------------------------------
if __name__ == '__main__':
    # Création des tables au démarrage
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
