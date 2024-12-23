from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import init_db
import sqlite3
from datetime import datetime
import requests

app = Flask(__name__)
app.secret_key = "super_secret_key"

# Flask-Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Flask-Login User class
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    """Load a user by ID for Flask-Login."""
    with sqlite3.connect('students.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (int(user_id),))
        user = cursor.fetchone()
    if user:
        return User(id=user["id"], username=user["username"], role=user["role"])
    return None

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('students.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):
            # Vérifiez si l'utilisateur a accepté les CGU mises à jour
            last_terms_update = datetime.strptime("2024-01-01", "%Y-%m-%d")  # Date de la dernière mise à jour
            accepted_terms = user["accepted_terms_date"]

            if not accepted_terms or datetime.strptime(accepted_terms, "%Y-%m-%d") < last_terms_update:
                flash("Veuillez accepter les nouvelles Conditions Générales d'Utilisation.", "warning")
                session['pending_accept_terms'] = user["id"]
                return redirect(url_for('terms_of_service'))

            login_user(User(id=user["id"], username=user["username"], role=user["role"]))
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'danger')

    return render_template('login.html')
    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Render dashboard based on the user's role or the role selected by admin."""
    # Vérifie si l'administrateur veut voir un autre rôle
    role = session.get('view_as_role', current_user.role)

    if role == "student":
        return redirect(url_for('student_dashboard', user_id=current_user.id))
    elif role == "teacher":
        return redirect(url_for('teacher_dashboard', user_id=current_user.id))
    elif role == "vie_scolaire":
        return redirect(url_for('vie_scolaire_dashboard', user_id=current_user.id))
    elif role == "admin":
        return redirect(url_for('admin_dashboard'))
    return "Invalid Role"

@app.route('/student_dashboard/<int:user_id>')
@login_required
def student_dashboard(user_id):
    """Affiche le tableau de bord d'un étudiant."""
    if current_user.role != 'admin' and current_user.id != user_id:
        return redirect(url_for('login'))

    with sqlite3.connect('students.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        student = cursor.fetchone()

    return render_template('student_dashboard.html', student=student)

@app.route('/teacher_dashboard/<int:user_id>')
@login_required
def teacher_dashboard(user_id):
    """Affiche le tableau de bord d'un enseignant."""
    if current_user.role != 'admin' and current_user.id != user_id:
        return redirect(url_for('login'))

    with sqlite3.connect('students.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        teacher = cursor.fetchone()

    return render_template('teacher_dashboard.html', teacher=teacher)

@app.route('/vie_scolaire_dashboard/<int:user_id>')
@login_required
def vie_scolaire_dashboard(user_id):
    """Affiche le tableau de bord de la vie scolaire."""
    if current_user.role != 'admin' and current_user.id != user_id:
        return redirect(url_for('login'))

    with sqlite3.connect('students.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        vie_scolaire = cursor.fetchone()

    return render_template('vie_scolaire_dashboard.html', vie_scolaire=vie_scolaire)
    
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    """Affiche la liste des utilisateurs dans le tableau de bord admin."""
    if current_user.role != 'admin':
        return redirect(url_for('login'))

    with sqlite3.connect('students.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

    return render_template('admin_dashboard.html', users=users)

@app.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    """Création d'un nouvel utilisateur (Admin uniquement)."""
    if current_user.role != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        hashed_password = generate_password_hash(password)

        with sqlite3.connect('students.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, role) 
                VALUES (?, ?, ?)
            ''', (username, hashed_password, role))
            conn.commit()
            flash('User created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))

    return render_template('create_user.html')

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Modifier un utilisateur existant (Admin uniquement)."""
    if current_user.role != 'admin':
        return redirect(url_for('login'))

    with sqlite3.connect('students.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        hashed_password = generate_password_hash(password)

        with sqlite3.connect('students.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users
                SET username = ?, password = ?, role = ?
                WHERE id = ?
            ''', (username, hashed_password, role, user_id))
            conn.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))

    return render_template('edit_user.html', user=user)

@app.route('/delete_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    """Supprimer un utilisateur (Admin uniquement)."""
    if current_user.role != 'admin':
        return redirect(url_for('login'))

    with sqlite3.connect('students.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        flash('User deleted successfully!', 'success')

    return redirect(url_for('admin_dashboard'))

@app.route('/view_as_role', methods=['POST'])
@login_required
def view_as_role():
    """Permet à l'administrateur de voir le site comme un autre rôle."""
    if current_user.role != 'admin':
        return redirect(url_for('login'))

    role = request.form['role']

    # Vérification que le rôle est valide
    if role not in ['student', 'teacher', 'vie_scolaire']:
        flash('Invalid role selected.', 'danger')
        return redirect(url_for('admin_dashboard'))

    # Stockage temporaire du rôle dans la session
    session['view_as_role'] = role

    flash(f'Now viewing as {role.capitalize()}.', 'success')

    # Passer l'user_id à la route dashboard
    return redirect(url_for('dashboard', user_id=current_user.id))

@app.route('/timetable/<int:user_id>')
@login_required
def timetable(user_id):
    """Display the timetable for a specific student."""
    # Fetch timetable data from the database based on user_id
    with sqlite3.connect('students.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM timetable WHERE user_id = ?", (user_id,))
        timetable = cursor.fetchall()
    
    return render_template('timetable.html', timetable=timetable)

@app.route('/add_task/<int:user_id>', methods=['GET', 'POST'])
@login_required
def add_task(user_id):
    """Allow a user to add a task."""
    if current_user.id != user_id and current_user.role != 'admin':
        return redirect(url_for('login'))

    # Handle adding the task logic here
    if request.method == 'POST':
        task_name = request.form['task_name']
        task_description = request.form['task_description']
        # Insert the task into the database for the specific user
        with sqlite3.connect('students.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO todo (user_id, task_name, task_description)
                VALUES (?, ?, ?)
            ''', (user_id, task_name, task_description))
            conn.commit()

        flash('Task added successfully!', 'success')
        return redirect(url_for('student_dashboard', user_id=user_id))

    return render_template('add_task.html', user_id=user_id)

@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 error page."""
    return render_template('404.html'), 404

@app.route('/forums')
@login_required
def forums():
    """Afficher les forums disponibles pour l'utilisateur."""
    with sqlite3.connect('students.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Forums globaux
        cursor.execute("SELECT * FROM forums WHERE is_global = 1")
        global_forums = cursor.fetchall()

        # Forums liés à l'utilisateur (classes et établissements)
        cursor.execute("""
            SELECT * FROM forums WHERE class_id IN (
                SELECT id FROM classes WHERE id = ?
            ) OR institution_id = ?
        """, (current_user.class_id, current_user.institution_id))
        local_forums = cursor.fetchall()

    return render_template('forums.html', global_forums=global_forums, local_forums=local_forums)


@app.route('/forum/<int:forum_id>', methods=['GET', 'POST'])
@login_required
def forum(forum_id):
    """Afficher un forum et permettre d'y poster des messages."""
    with sqlite3.connect('students.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Charger le forum et ses messages
        cursor.execute("SELECT * FROM forums WHERE id = ?", (forum_id,))
        forum = cursor.fetchone()

        if request.method == 'POST':
            content = request.form['content']
            cursor.execute("""
                INSERT INTO messages (user_id, forum_id, content) VALUES (?, ?, ?)
            """, (current_user.id, forum_id, content))
            conn.commit()
            flash('Message posted!', 'success')

        cursor.execute("""
            SELECT messages.*, users.username FROM messages
            JOIN users ON messages.user_id = users.id
            WHERE forum_id = ? ORDER BY timestamp ASC
        """, (forum_id,))
        messages = cursor.fetchall()

    return render_template('forum.html', forum=forum, messages=messages)

@app.route('/moderate/forums')
@login_required
def moderate_forums():
    """Liste des forums pour la modération."""
    if current_user.role not in ['admin', 'moderator']:
        return redirect(url_for('dashboard'))

    with sqlite3.connect('students.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM forums")
        forums = cursor.fetchall()

    return render_template('moderate_forums.html', forums=forums)


@app.route('/moderate/forums/delete/<int:forum_id>', methods=['POST'])
@login_required
def delete_forum(forum_id):
    """Supprimer un forum (Modérateur/Admin uniquement)."""
    if current_user.role not in ['admin', 'moderator']:
        return redirect(url_for('dashboard'))

    with sqlite3.connect('students.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM forums WHERE id = ?", (forum_id,))
        conn.commit()
        flash('Forum deleted successfully!', 'success')

    return redirect(url_for('moderate_forums'))


@app.route('/moderate/users/ban/<int:user_id>', methods=['POST'])
@login_required
def ban_user(user_id):
    """Bannir un utilisateur (Modérateur/Admin uniquement)."""
    if current_user.role not in ['admin', 'moderator']:
        return redirect(url_for('dashboard'))

    with sqlite3.connect('students.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET role = 'banned' WHERE id = ?
        """, (user_id,))
        conn.commit()
        flash('User banned successfully!', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/create_class', methods=['GET', 'POST'])
@login_required
def create_class():
    """Créer une classe (Admin uniquement)."""
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        institution_id = current_user.institution_id

        with sqlite3.connect('students.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO classes (name, institution_id) VALUES (?, ?)", (name, institution_id))
            conn.commit()
            flash('Class created successfully!', 'success')

    return render_template('create_class.html')


@app.route('/create_institution', methods=['GET', 'POST'])
@login_required
def create_institution():
    """Créer un établissement (Admin uniquement)."""
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']

        with sqlite3.connect('students.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO institutions (name, address) VALUES (?, ?)", (name, address))
            conn.commit()
            flash('Institution created successfully!', 'success')

    return render_template('create_institution.html')

@app.route('/terms-of-service')
def terms_of_service():
    """Afficher les Conditions Générales d'Utilisation."""
    return render_template('terms_of_service.html')

@app.route('/legal-notice')
def legal_notice():
    """Afficher les Mentions Légales."""
    return render_template('legal_notice.html')

@app.route('/privacy-policy')
def privacy_policy():
    """Afficher la Politique de Confidentialité."""
    return render_template('privacy_policy.html')

@app.route('/select_app', methods=['GET', 'POST'])
@login_required
def select_app():
    """Permettre à l'utilisateur de choisir entre Pronote ou École Directe."""
    if request.method == 'POST':
        selected_app = request.form['app_choice']
        session['selected_app'] = selected_app  # Sauvegarder l'application choisie

        # Redirection en fonction de l'application sélectionnée
        if selected_app == 'pronote':
            return redirect(url_for('connect_pronote'))
        elif selected_app == 'ecole_directe':
            return redirect(url_for('connect_ecole_directe'))

        flash('Application invalide sélectionnée.', 'danger')

    return render_template('select_app.html')

@app.route('/connect_pronote', methods=['GET', 'POST'])
@login_required
def connect_pronote():
    """Connexion à Pronote via ses identifiants."""
    if request.method == 'POST':
        pronote_url = request.form['url']
        username = request.form['username']
        password = request.form['password']

        try:
            # Exemple d'appel à l'API Pronote (library "pronotepy" requise)
            import pronotepy
            client = pronotepy.Client(pronote_url, username, password)

            if client.is_logged_in:
                session['pronote_data'] = client.info  # Sauvegarder les données récupérées
                flash('Connexion réussie à Pronote!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Connexion échouée à Pronote. Vérifiez vos identifiants.', 'danger')

        except Exception as e:
            flash(f'Erreur lors de la connexion à Pronote : {e}', 'danger')

    return render_template('connect_pronote.html')

@app.route('/display_data')
@login_required
def display_data():
    """Afficher les données récupérées via Pronote ou École Directe."""
    selected_app = session.get('selected_app')

    if selected_app == 'pronote':
        data = session.get('pronote_data', {})
        return render_template('display_pronote_data.html', data=data)

    elif selected_app == 'ecole_directe':
        data = session.get('ecole_directe_data', {})
        return render_template('display_ecole_directe_data.html', data=data)

    flash('Aucune donnée disponible. Connectez-vous à une application.', 'danger')
    return redirect(url_for('select_app'))

# Run the app and initialize the database
if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True, host='0.0.0.0', port=5000)