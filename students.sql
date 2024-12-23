PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;
CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL -- student, teacher, vie_scolaire, admin
        );
INSERT INTO users VALUES(1,'vik_srhk','scrypt:32768:8:1$UtZHyEPh2aVG3jiH$eda417a4a800dee73ffe25ce4c37e5546fdf4b1d1bc51bce8b4654a0f5a6901fc8278ebaf985d6c03a9e1803dcc1d06fa03f21a6b0ddda5083c50682c9d37f1f','admin');
INSERT INTO users VALUES(2,'pouchin_14','scrypt:32768:8:1$PZpO7lKy1a5qu00f$f9f8aad29ffa44bc119fe6e7a77bc2933972be5c7681fad12d7003ca6213d9f543a6ccd3fcced24f2d7fa422dcc09bdca40cc99988ff33452498fc505ff98f29','teacher');
INSERT INTO users VALUES(3,'noa_die','scrypt:32768:8:1$jLT864hbgNFjStDF$102003708b4ba003a1b053104f64dfd368c6b7e71a553e6554aa95af3d0ccd8c1d29ba50735232f6b8595beba3a4a721b103470caaa42e6d943af147e124f415','student');
INSERT INTO users VALUES(4,'gab_prvsn','scrypt:32768:8:1$SiNVMJNBQiYcB34F$48c6e1c156b675d6d66405381fdc8e509a1526d0600da244d419d7bdbd30e79efe0435033aa67abdfaba4d25a55be546b9e68fea974ce62bf96719132e1db07b','student');
CREATE TABLE students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            class TEXT NOT NULL,
            institution_id INTEGER, -- Nouvelle colonne
            FOREIGN KEY (institution_id) REFERENCES institutions(id)
        );
CREATE TABLE grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            grade REAL NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        );
CREATE TABLE timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            day TEXT NOT NULL, -- Monday, Tuesday, etc.
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            subject TEXT NOT NULL,
            room TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
CREATE TABLE todo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    task_name TEXT NOT NULL,
    task_description TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE institutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    address TEXT
);

CREATE TABLE classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    institution_id INTEGER NOT NULL,
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);

CREATE TABLE forums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    class_id INTEGER, -- NULL pour les forums globaux
    institution_id INTEGER, -- NULL pour les forums globaux
    is_global BOOLEAN DEFAULT 0,
    FOREIGN KEY (class_id) REFERENCES classes(id),
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    forum_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (forum_id) REFERENCES forums(id)
);

INSERT INTO todo VALUES(1,1,'homework','french lesson');
INSERT INTO todo VALUES(2,1,'homework','french lesson');
INSERT INTO todo VALUES(3,1,'xcc','gvff');
INSERT INTO todo VALUES(4,3,'noemyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy','163');
INSERT INTO todo VALUES(5,3,'noemyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy','163');
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('users',4);
INSERT INTO sqlite_sequence VALUES('todo',5);
COMMIT;
PRAGMA foreign_keys=OFF;