import sqlite3

DATABASE_FILE = "students.db"

def get_connection():
    """
    Establish a connection to the SQLite database.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # Enable named column access
    return conn

def init_db():
    """
    Initialize the database by creating all necessary tables.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL -- student, teacher, vie_scolaire, admin
        )
        ''')
        
        # Students table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            class TEXT NOT NULL
        )
        ''')
        
        # Grades table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            grade REAL NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        )
        ''')
        
        # Timetable table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, -- Can be student or teacher
            day TEXT NOT NULL, -- Monday, Tuesday, etc.
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            subject TEXT NOT NULL,
            room TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        ''')
        
        # To-Do List table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS todo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, -- Only for students
            task_name TEXT NOT NULL,
            
            task TEXT NOT NULL,
            status TEXT DEFAULT 'pending', -- pending or completed
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        ''')
        
        conn.commit()
        print("Database initialized!")

def query_db(query, args=(), one=False):
    """
    Utility function to execute a query on the database.
    """
    with get_connection() as conn:
        cursor = conn.execute(query, args)
        results = cursor.fetchall()
        return (results[0] if results else None) if one else results

def insert_or_update(query, args=()):
    """
    Utility function to execute an INSERT or UPDATE query.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, args)
        conn.commit()
        return cursor.lastrowid