from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_socketio import SocketIO, emit
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_unsafe_key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['WTF_CSRF_ENABLED'] = True

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
socketio = SocketIO(app)
bcrypt = Bcrypt(app)

CHUNK_SIZE = 50  # Size of a chunk in cells

# Handle CSRF errors
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash("Security error: your session has expired or the request is invalid.", "danger")
    return redirect(url_for("login"))

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

# Chunk model to manage grid data
class Chunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chunk_x = db.Column(db.Integer, nullable=False)
    chunk_y = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Text, nullable=False)  # Chunk data, serialized

# Define the login form
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

# Initialize the database
with app.app_context():
    db.create_all()

# Homepage
@app.route("/")
def index():
    return render_template("index.html")

# Registration page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(email=email).first():
            flash("Email already in use!", "danger")
            return redirect(url_for("register"))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful!", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Login successful!", "success")
            return redirect(url_for("game", x=0, y=0))
        flash("Incorrect email or password", "danger")
    return render_template("login.html", form=form)

# Game page
@app.route("/game", defaults={'x': 0, 'y': 0}, methods=["GET"])
@app.route("/game/<int:x>/<int:y>", methods=["GET"])
def game(x, y):
    if 'user_id' not in session:
        flash("You must be logged in to play!", "danger")
        return redirect(url_for("login"))

    return render_template("game.html", x=x, y=y)

# API to retrieve a chunk
@app.route('/api/get_chunk', methods=['GET'])
def get_chunk():
    chunk_x = int(request.args.get('chunk_x'))
    chunk_y = int(request.args.get('chunk_y'))
    chunk = Chunk.query.filter_by(chunk_x=chunk_x, chunk_y=chunk_y).first()
    if not chunk:
        return jsonify({"chunk_x": chunk_x, "chunk_y": chunk_y, "data": " " * (CHUNK_SIZE ** 2)}), 200, {'Content-Type': 'application/json'}
    return jsonify({"chunk_x": chunk.chunk_x, "chunk_y": chunk.chunk_y, "data": chunk.data}), 200, {'Content-Type': 'application/json'}

# WebSocket: receive and broadcast modifications
@socketio.on('update_cell')
def handle_update(data):
    chunk_x, chunk_y = data['chunk_x'], data['chunk_y']
    cell_x, cell_y = data['cell_x'], data['cell_y']
    character = data['character']

    # Update the chunk in the database
    chunk = Chunk.query.filter_by(chunk_x=chunk_x, chunk_y=chunk_y).first()
    if not chunk:
        chunk = Chunk(chunk_x=chunk_x, chunk_y=chunk_y, data=" " * (CHUNK_SIZE ** 2))
        db.session.add(chunk)

    chunk_data = list(chunk.data)
    index = cell_y * CHUNK_SIZE + cell_x
    chunk_data[index] = character
    chunk.data = "".join(chunk_data)
    db.session.commit()

    # Broadcast the modification
    emit('cell_updated', data, broadcast=True)

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Log in to access the dashboard", "warning")
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# Logout
@app.route("/logout")
def logout():
    session.pop('user_id', None)
    flash("You are now logged out.", "info")
    return redirect(url_for("index"))

if __name__ == "__main__":
    socketio.run(app, debug=True)