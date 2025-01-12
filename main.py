from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_unsafe_key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['WTF_CSRF_ENABLED'] = True

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
socketio = SocketIO(app)

CHUNK_SIZE = 50  # Taille d'un chunk en cases

# Gestionnaire d'erreur CSRF
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash("Erreur de sécurité : votre session a expiré ou la requête est invalide.", "danger")
    return redirect(url_for("login"))

# Modèle utilisateur
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

# Modèle Chunk pour gérer les données de la grille
class Chunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chunk_x = db.Column(db.Integer, nullable=False)
    chunk_y = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Text, nullable=False)  # Données du chunk, sérialisées

# Initialisation de la base de données
with app.app_context():
    db.create_all()

# Page d'accueil
@app.route("/")
def index():
    return render_template("index.html")

# Page d'inscription
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(email=email).first():
            flash("Email déjà utilisé !", "danger")
            return redirect(url_for("register"))

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Inscription réussie !", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# Page de connexion
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            session['user_id'] = user.id
            flash("Connexion réussie !", "success")
            return redirect(url_for("game", x=0, y=0))
        flash("Email ou mot de passe incorrect", "danger")
    return render_template("login.html")

# Page de jeu
@app.route("/game", defaults={'x': 0, 'y': 0}, methods=["GET"])
@app.route("/game/<int:x>/<int:y>", methods=["GET"])
def game(x, y):
    if 'user_id' not in session:
        flash("Vous devez être connecté pour jouer !", "danger")
        return redirect(url_for("login"))

    return render_template("game.html", x=x, y=y)

# API pour récupérer un chunk
@app.route('/api/get_chunk', methods=['GET'])
def get_chunk():
    chunk_x = int(request.args.get('chunk_x'))
    chunk_y = int(request.args.get('chunk_y'))
    chunk = Chunk.query.filter_by(chunk_x=chunk_x, chunk_y=chunk_y).first()
    if not chunk:
        return jsonify({"chunk_x": chunk_x, "chunk_y": chunk_y, "data": " " * (CHUNK_SIZE ** 2)})
    return jsonify({"chunk_x": chunk.chunk_x, "chunk_y": chunk.chunk_y, "data": chunk.data})

# WebSocket : recevoir et diffuser des modifications
@socketio.on('update_cell')
def handle_update(data):
    chunk_x, chunk_y = data['chunk_x'], data['chunk_y']
    cell_x, cell_y = data['cell_x'], data['cell_y']
    character = data['character']

    # Mettre à jour le chunk dans la base
    chunk = Chunk.query.filter_by(chunk_x=chunk_x, chunk_y=chunk_y).first()
    if not chunk:
        chunk = Chunk(chunk_x=chunk_x, chunk_y=chunk_y, data=" " * (CHUNK_SIZE ** 2))
        db.session.add(chunk)

    chunk_data = list(chunk.data)
    index = cell_y * CHUNK_SIZE + cell_x
    chunk_data[index] = character
    chunk.data = "".join(chunk_data)
    db.session.commit()

    # Diffuser la modification
    emit('cell_updated', data, broadcast=True)

# Déconnexion
@app.route("/logout")
def logout():
    session.pop('user_id', None)
    flash("Vous êtes maintenant déconnecté.", "info")
    return redirect(url_for("index"))

if __name__ == "__main__":
    socketio.run(app, debug=True)
