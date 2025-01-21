from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from PIL import Image

app = Flask(__name__)

# Configurer PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@db:5432/facial_recognition_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modèle pour stocker les résultats
class ComparisonResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    known_image = db.Column(db.String(256), nullable=False)
    unknown_image = db.Column(db.String(256), nullable=False)
    match = db.Column(db.Boolean, nullable=False)
    distance = db.Column(db.Float, nullable=False)
    
# Charger le modèle FaceNet depuis TensorFlow Hub
model_url = "https://tfhub.dev/google/imagenet/mobilenet_v2_100_224/classification/5"
facenet_model = hub.load(model_url)


# Fonction pour prétraiter les images
def preprocess_image(image_path):
    image = Image.open(image_path).convert('RGB')
    image = image.resize((224, 224))  # Taille requise par FaceNet
    image = np.array(image) / 255.0  # Normalisation
    return np.expand_dims(image.astype('float32'), axis=0)  # Ajouter une dimension batch

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/status', methods=['GET'])
def status():
    return "API is running!"

# Fonction pour extraire les encodages faciaux
def get_face_encoding(image_path):
    preprocessed_image = preprocess_image(image_path)
    encoding = facenet_model(preprocessed_image)
    return encoding.numpy()

# Fonction pour comparer deux visages
def compare_faces(known_image_path, unknown_image_path, threshold=0.6):
    known_encoding = get_face_encoding(known_image_path)
    unknown_encoding = get_face_encoding(unknown_image_path)
    distance = np.linalg.norm(known_encoding - unknown_encoding)
    is_match = distance < threshold
    return is_match, distance


@app.route('/upload', methods=['POST'])
def upload_images():
    try:
        known_file = request.files['known_image']
        unknown_file = request.files['unknown_image']
        
        # Sauvegarder temporairement les fichiers
        known_path = "known_temp.jpg"
        unknown_path = "unknown_temp.jpg"
        known_file.save(known_path)
        unknown_file.save(unknown_path)

        # Comparer les visages
        is_match, distance = compare_faces(known_path, unknown_path)

        # Sauvegarder les résultats dans la base de données
        result = ComparisonResult(
            known_image=known_file.filename,
            unknown_image=unknown_file.filename,
            match=is_match,
            distance=float(distance)  # Convertir pour éviter les erreurs JSON
        )
        db.session.add(result)
        db.session.commit()

        return jsonify({'match': is_match, 'distance': distance})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
