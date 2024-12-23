import sqlite3
from werkzeug.security import generate_password_hash

def create_admin_user():
    username = "vik_srhk"
    password = "V1023210232r"  # Change this to a secure password
    hashed_password = generate_password_hash(password)
    role = "admin"

    with sqlite3.connect('students.db') as conn:
        cursor = conn.cursor()

        # Assure que la table "users" existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')

        # Insère l'utilisateur admin
        try:
            cursor.execute('''
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
            ''', (username, hashed_password, role))
            conn.commit()
            print(f"Admin user '{username}' created successfully!")
        except sqlite3.IntegrityError:
            print("Admin user already exists!")

# Appelle la fonction pour créer l'utilisateur admin
create_admin_user()