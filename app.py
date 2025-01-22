from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import os
import uuid
import json
import numpy as np
from datetime import datetime
# ----- DeepFace pour la reconnaissance faciale -----
from deepface import DeepFace

app = Flask(__name__)

# ---------- Clé secrète pour JWT ----------
app.config['JWT_SECRET_KEY'] = 'supersecret'
jwt = JWTManager(app)

# Route pour générer un token JWT
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    # Vérifiez les infos d'identification
    if username != 'test' or password != 'test':
        return jsonify({"msg": "Bad username or password"}), 401

    # Créez un nouveau token d'accès
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)

# Exemple de route protégée
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # Cette fonction current_user n'est pas définie dans ton code,
    # donc on la commente ou on la remplace par un message générique
    return jsonify(logged_in_as="some_user"), 200

# ---------------------------------------------------------------------
# Configuration MySQL (adaptée à Docker Compose)
# ---------------------------------------------------------------------
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:password@localhost:3306/facial_recognition"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ----------------------------------------------------
# Modèle Employee : on stocke le nom et l'embedding
# ----------------------------------------------------
class Employee(db.Model):
    __tablename__ = 'employee'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    embedding = db.Column(db.Text, nullable=False)  # Stocke l'embedding en JSON

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
        model_name="Facenet",  # ou "Facenet512"
        detector_backend="mtcnn"
    )
    return embedding_vector

# ----------------------------------------------------
# Page d'accueil avec deux formulaires
# ----------------------------------------------------
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

# ----------------------------------------------------
# Route pour enregistrer un nouvel employé
# ----------------------------------------------------
@app.route('/register', methods=['POST'])
def register_employee():
    name = request.form.get("name")
    if "image" not in request.files or not name:
        return jsonify({"error": "Missing 'name' or 'image' in the form-data."}), 400

    image_file = request.files["image"]
    temp_path = f"temp_{uuid.uuid4()}.jpg"
    image_file.save(temp_path)

    try:
        # Obtenir l'embedding depuis DeepFace
        raw_embedding = get_face_embedding(temp_path)
        
        # Forcer la conversion au type float Python
        embedding = [float(x) for x in raw_embedding]

    except Exception as e:
        os.remove(temp_path)
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Sérialiser en JSON sans erreur
    embedding_json = json.dumps(embedding)

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
    Attend un fichier 'image':
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
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Charger tous les employés
    employees = Employee.query.all()
    unknown_emb_array = np.array(unknown_emb)

    best_match = None
    best_distance = float("inf")  # Python float

    # Seuil empirique
    threshold = 10.0

    for emp in employees:
        emp_emb_array = np.array(json.loads(emp.embedding))
        dist = np.linalg.norm(unknown_emb_array - emp_emb_array)
        if dist < best_distance:
            best_distance = dist
            best_match = emp

    # Convertir best_distance en float Python standard pour la sérialisation JSON
    best_distance = float(best_distance)

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
    # Créer les tables au démarrage
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
