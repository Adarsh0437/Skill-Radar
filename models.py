from functools import wraps
import os
import sqlite3
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import psycopg2
from psycopg2 import OperationalError as PostgresOperationalError
from psycopg2.extras import RealDictCursor

from flask import abort
from flask_login import UserMixin, current_user
from werkzeug.security import check_password_hash, generate_password_hash


SKILL_FIELDS = [
    "python",
    "sql",
    "java",
    "dsa",
    "communication",
    "problem_solving",
    "web_dev",
    "ml",
]

DB_PATH = os.getenv("DB_PATH", "instance/skillradar.db")
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


class DatabaseOperationalError(Exception):
    """Raised when the database is unavailable or the schema cannot be updated."""


class DatabaseIntegrityError(Exception):
    """Raised when a unique or relational constraint fails."""


def resolve_database_url(app=None):
    if app is not None and getattr(app, "config", None):
        return (app.config.get("DATABASE_URL") or "").strip()
    return DATABASE_URL


def resolve_db_path(app=None):
    if app is not None and getattr(app, "config", None):
        return app.config.get("DB_PATH", DB_PATH)
    return DB_PATH


def get_db_backend(app=None):
    return "postgres" if resolve_database_url(app) else "sqlite"


def _postgres_dsn(database_url):
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        return database_url

    query = dict(parse_qsl(parsed.query))
    query.setdefault("sslmode", "require")
    return urlunparse(parsed._replace(query=urlencode(query)))


class User(UserMixin):
    def __init__(self, record):
        if isinstance(record, dict):
            self.id = record["id"]
            self.name = record["name"]
            self.email = record["email"]
            self.password_hash = record["password_hash"]
            self.role = record["role"]
            self.cgpa = record["cgpa"]
            self.roll_number = record["roll_number"]
            self.department = record["department"]
            self.passout_year = record.get("passout_year")
            self.created_at = record["created_at"]


def get_connection(app=None):
    backend = get_db_backend(app)
    if backend == "postgres":
        try:
            conn = psycopg2.connect(_postgres_dsn(resolve_database_url(app)))
        except PostgresOperationalError as exc:
            raise DatabaseOperationalError("Unable to connect to PostgreSQL.") from exc
        return conn

    db_path = resolve_db_path(app)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _prepare_query(app, query):
    if get_db_backend(app) == "postgres":
        return query.replace("?", "%s")
    return query


def dict_from_row(row):
    if row is None:
        return None
    return dict(row)


def fetch_one(app, query, params=None):
    conn = get_connection(app)
    try:
        if get_db_backend(app) == "postgres":
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(_prepare_query(app, query), params or ())
                result = cursor.fetchone()
                return dict(result) if result else None
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        result = cursor.fetchone()
        return dict_from_row(result) if result else None
    finally:
        conn.close()


def fetch_all(app, query, params=None):
    conn = get_connection(app)
    try:
        if get_db_backend(app) == "postgres":
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(_prepare_query(app, query), params or ())
                return [dict(row) for row in cursor.fetchall()]
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        return [dict_from_row(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def execute_query(app, query, params=None):
    conn = get_connection(app)
    try:
        backend = get_db_backend(app)
        prepared_query = _prepare_query(app, query)
        if backend == "postgres":
            with conn.cursor() as cursor:
                cursor.execute(prepared_query, params or ())
                inserted_id = None
                if " returning " in prepared_query.lower():
                    row = cursor.fetchone()
                    if row:
                        inserted_id = row[0]
                conn.commit()
                return inserted_id

        cursor = conn.cursor()
        cursor.execute(prepared_query, params or ())
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise DatabaseIntegrityError(str(exc)) from exc
    except psycopg2.IntegrityError as exc:
        conn.rollback()
        raise DatabaseIntegrityError(str(exc)) from exc
    except sqlite3.OperationalError as exc:
        conn.rollback()
        raise DatabaseOperationalError(str(exc)) from exc
    except PostgresOperationalError as exc:
        conn.rollback()
        raise DatabaseOperationalError(str(exc)) from exc
    finally:
        conn.close()


def ensure_users_table(app=None):
    if get_db_backend(app) == "postgres":
        query = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'officer')),
                cgpa NUMERIC(3,2) DEFAULT NULL,
                roll_number VARCHAR(50) DEFAULT NULL UNIQUE,
                department VARCHAR(100) DEFAULT NULL,
                passout_year INTEGER DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    else:
        query = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(120) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'officer')),
                cgpa DECIMAL(3,2) DEFAULT NULL,
                roll_number VARCHAR(50) DEFAULT NULL UNIQUE,
                department VARCHAR(100) DEFAULT NULL,
                passout_year INTEGER DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    execute_query(app, query)


def ensure_users_columns(app=None):
    if get_db_backend(app) == "postgres":
        columns = fetch_all(
            app,
            """
            SELECT column_name AS name
            FROM information_schema.columns
            WHERE table_name = 'users'
            """,
        )
    else:
        columns = fetch_all(app, "PRAGMA table_info(users)")
    column_names = {column["name"] for column in columns}
    if "passout_year" not in column_names:
        execute_query(app, "ALTER TABLE users ADD COLUMN passout_year INTEGER DEFAULT NULL")


def migrate_skills_table_to_zero_scale(app=None):
    if get_db_backend(app) != "sqlite":
        return

    ensure_app_meta_table(app)
    already_migrated = fetch_one(
        app,
        "SELECT meta_key FROM app_meta WHERE meta_key = ?",
        ("skills_zero_scale_v1",),
    )
    if already_migrated:
        return

    schema_row = fetch_one(
        app,
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
        ("skills",),
    )
    if not schema_row:
        return

    schema_sql = (schema_row.get("sql") or "").upper()
    if "BETWEEN 1 AND 10" in schema_sql or "DEFAULT 1" in schema_sql:
        execute_query(app, "ALTER TABLE skills RENAME TO skills_old")
        ensure_skills_table(app)
        execute_query(
            app,
            """
            INSERT INTO skills (id, user_id, python, sql, java, dsa, communication, problem_solving, web_dev, ml, updated_at)
            SELECT id, user_id, python, sql, java, dsa, communication, problem_solving, web_dev, ml, updated_at
            FROM skills_old
            """,
        )
        execute_query(app, "DROP TABLE skills_old")

    execute_query(
        app,
        "INSERT INTO app_meta (meta_key, meta_value) VALUES (?, ?)",
        ("skills_zero_scale_v1", "done"),
    )


def ensure_skills_table(app=None):
    if get_db_backend(app) == "postgres":
        query = """
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                python SMALLINT NOT NULL DEFAULT 0,
                sql SMALLINT NOT NULL DEFAULT 0,
                java SMALLINT NOT NULL DEFAULT 0,
                dsa SMALLINT NOT NULL DEFAULT 0,
                communication SMALLINT NOT NULL DEFAULT 0,
                problem_solving SMALLINT NOT NULL DEFAULT 0,
                web_dev SMALLINT NOT NULL DEFAULT 0,
                ml SMALLINT NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (python BETWEEN 0 AND 10),
                CHECK (sql BETWEEN 0 AND 10),
                CHECK (java BETWEEN 0 AND 10),
                CHECK (dsa BETWEEN 0 AND 10),
                CHECK (communication BETWEEN 0 AND 10),
                CHECK (problem_solving BETWEEN 0 AND 10),
                CHECK (web_dev BETWEEN 0 AND 10),
                CHECK (ml BETWEEN 0 AND 10)
            )
        """
    else:
        query = """
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                python TINYINT NOT NULL DEFAULT 0,
                sql TINYINT NOT NULL DEFAULT 0,
                java TINYINT NOT NULL DEFAULT 0,
                dsa TINYINT NOT NULL DEFAULT 0,
                communication TINYINT NOT NULL DEFAULT 0,
                problem_solving TINYINT NOT NULL DEFAULT 0,
                web_dev TINYINT NOT NULL DEFAULT 0,
                ml TINYINT NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                CHECK (python BETWEEN 0 AND 10),
                CHECK (sql BETWEEN 0 AND 10),
                CHECK (java BETWEEN 0 AND 10),
                CHECK (dsa BETWEEN 0 AND 10),
                CHECK (communication BETWEEN 0 AND 10),
                CHECK (problem_solving BETWEEN 0 AND 10),
                CHECK (web_dev BETWEEN 0 AND 10),
                CHECK (ml BETWEEN 0 AND 10)
            )
        """
    execute_query(app, query)


def ensure_companies_table(app=None):
    if get_db_backend(app) == "postgres":
        query = """
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                role VARCHAR(120) NOT NULL,
                ctc_lpa NUMERIC(5,2) NOT NULL,
                min_cgpa NUMERIC(3,2) NOT NULL,
                skills_required VARCHAR(255) NOT NULL,
                drive_date DATE NOT NULL,
                prep_kit_url VARCHAR(255) NOT NULL
            )
        """
    else:
        query = """
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(120) NOT NULL,
                role VARCHAR(120) NOT NULL,
                ctc_lpa DECIMAL(5,2) NOT NULL,
                min_cgpa DECIMAL(3,2) NOT NULL,
                skills_required VARCHAR(255) NOT NULL,
                drive_date DATE NOT NULL,
                prep_kit_url VARCHAR(255) NOT NULL
            )
        """
    execute_query(app, query)


def ensure_contact_settings_table(app=None):
    if get_db_backend(app) == "postgres":
        create_query = """
            CREATE TABLE IF NOT EXISTS contact_settings (
                id INTEGER PRIMARY KEY,
                map_embed_url VARCHAR(500) NOT NULL,
                office_address VARCHAR(255) NOT NULL,
                phone VARCHAR(50) NOT NULL,
                email VARCHAR(150) NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    else:
        create_query = """
            CREATE TABLE IF NOT EXISTS contact_settings (
                id INTEGER PRIMARY KEY,
                map_embed_url VARCHAR(500) NOT NULL,
                office_address VARCHAR(255) NOT NULL,
                phone VARCHAR(50) NOT NULL,
                email VARCHAR(150) NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    execute_query(app, create_query)

    existing = fetch_one(app, "SELECT id FROM contact_settings WHERE id = 1")
    if not existing:
        seed_query = """
            INSERT INTO contact_settings (id, map_embed_url, office_address, phone, email)
            VALUES (?, ?, ?, ?, ?)
        """
        execute_query(
            app,
            seed_query,
            (
                1,
                "https://www.google.com/maps?q=Indian%20Institute%20of%20Technology%20Madras&output=embed",
                "Academic Block C, Knowledge Avenue, Chennai 600036",
                "+91 44 2257 8900",
                "placements@skillradar.edu",
            ),
        )


def ensure_app_meta_table(app=None):
    if get_db_backend(app) == "postgres":
        query = """
            CREATE TABLE IF NOT EXISTS app_meta (
                meta_key VARCHAR(150) PRIMARY KEY,
                meta_value VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    else:
        query = """
            CREATE TABLE IF NOT EXISTS app_meta (
                meta_key VARCHAR(150) PRIMARY KEY,
                meta_value VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    execute_query(app, query)


def get_contact_settings(app):
    ensure_contact_settings_table(app)
    return fetch_one(app, "SELECT * FROM contact_settings WHERE id = 1")


def update_contact_settings(app, map_embed_url, office_address, phone, email):
    ensure_contact_settings_table(app)
    query = """
        UPDATE contact_settings
        SET map_embed_url = ?, office_address = ?, phone = ?, email = ?
        WHERE id = 1
    """
    execute_query(app, query, (map_embed_url, office_address, phone, email))


def ensure_schema(app=None):
    if get_db_backend(app) == "sqlite":
        db_path = resolve_db_path(app)
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    ensure_users_table(app)
    ensure_users_columns(app)
    ensure_skills_table(app)
    migrate_skills_table_to_zero_scale(app)
    ensure_companies_table(app)
    ensure_contact_settings_table(app)
    ensure_app_meta_table(app)
    ensure_alumni_mentors_table(app)
    seed_default_users(app)
    seed_default_skill_profiles(app)


def seed_default_users(app=None):
    officer = fetch_one(app, "SELECT id FROM users WHERE email = ?", ("officer@campus.edu",))
    if not officer:
        query = """
            INSERT INTO users (name, email, password_hash, role, cgpa, roll_number, department, passout_year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        execute_query(
            app,
            query,
            (
                "Placement Officer",
                "officer@campus.edu",
                generate_password_hash("admin123"),
                "officer",
                None,
                None,
                "Placement Cell",
                None,
            ),
        )

    student1 = fetch_one(app, "SELECT id FROM users WHERE email = ?", ("student1@campus.edu",))
    if not student1:
        query = """
            INSERT INTO users (name, email, password_hash, role, cgpa, roll_number, department, passout_year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        execute_query(
            app,
            query,
            (
                "Aarav Sharma",
                "student1@campus.edu",
                generate_password_hash("pass123"),
                "student",
                8.20,
                "CSE2024001",
                "Computer Science",
                2024,
            ),
        )

    student2 = fetch_one(app, "SELECT id FROM users WHERE email = ?", ("student2@campus.edu",))
    if not student2:
        query = """
            INSERT INTO users (name, email, password_hash, role, cgpa, roll_number, department, passout_year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        execute_query(
            app,
            query,
            (
                "Diya Nair",
                "student2@campus.edu",
                generate_password_hash("pass123"),
                "student",
                7.40,
                "ECE2024007",
                "Electronics",
                2024,
            ),
        )


def seed_default_skill_profiles(app=None):
    ensure_users_table(app)
    ensure_skills_table(app)
    ensure_app_meta_table(app)

    already_seeded = fetch_one(
        app,
        "SELECT meta_key FROM app_meta WHERE meta_key = ?",
        ("default_skill_profiles_seeded_v2",),
    )
    if already_seeded:
        return

    insert_query = """
        INSERT INTO skills (
            user_id, python, sql, java, dsa, communication, problem_solving, web_dev, ml
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    update_query = """
        UPDATE skills
        SET python = ?, sql = ?, java = ?, dsa = ?, communication = ?, problem_solving = ?, web_dev = ?, ml = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """
    profile_by_email = {
        "student1@campus.edu": (0, 7, 5, 6, 8, 6, 5, 4),
        "student2@campus.edu": (6, 0, 7, 5, 6, 8, 4, 5),
    }
    balanced_profiles = [
        (7, 6, 5, 6, 7, 6, 5, 4),
        (6, 5, 7, 5, 6, 8, 4, 5),
        (5, 7, 6, 6, 5, 7, 6, 4),
        (6, 4, 5, 7, 8, 5, 6, 3),
    ]

    named_students = fetch_all(
        app,
        """
        SELECT id, email
        FROM users
        WHERE role = 'student' AND email IN (?, ?)
        ORDER BY created_at ASC, id ASC
        """,
        tuple(profile_by_email.keys()),
    )
    for student in named_students:
        existing_skill = fetch_one(app, "SELECT user_id FROM skills WHERE user_id = ?", (student["id"],))
        default_values = profile_by_email[student["email"].lower()]
        if existing_skill:
            execute_query(app, update_query, (*default_values, student["id"]))
        else:
            execute_query(app, insert_query, (student["id"], *default_values))

    students_without_skills = fetch_all(
        app,
        """
        SELECT u.id, u.email
        FROM users u
        LEFT JOIN skills s ON s.user_id = u.id
        WHERE u.role = 'student' AND s.user_id IS NULL
        ORDER BY u.created_at ASC, u.id ASC
        """,
    )
    for index, student in enumerate(students_without_skills):
        if student.get("email", "").lower() in profile_by_email:
            continue
        default_values = balanced_profiles[index % len(balanced_profiles)]
        execute_query(app, insert_query, (student["id"], *default_values))

    execute_query(
        app,
        "INSERT INTO app_meta (meta_key, meta_value) VALUES (?, ?)",
        ("default_skill_profiles_seeded_v2", "done"),
    )


def ensure_alumni_mentors_table(app=None):
    if get_db_backend(app) == "postgres":
        create_query = """
            CREATE TABLE IF NOT EXISTS alumni_mentors (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                batch VARCHAR(80) NOT NULL,
                company VARCHAR(120) NOT NULL,
                linkedin VARCHAR(255) NOT NULL,
                email VARCHAR(150) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    else:
        create_query = """
            CREATE TABLE IF NOT EXISTS alumni_mentors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(120) NOT NULL,
                batch VARCHAR(80) NOT NULL,
                company VARCHAR(120) NOT NULL,
                linkedin VARCHAR(255) NOT NULL,
                email VARCHAR(150) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    execute_query(app, create_query)

    count_row = fetch_one(app, "SELECT COUNT(*) AS total FROM alumni_mentors")
    if count_row and count_row["total"] == 0:
        seed_query = """
            INSERT INTO alumni_mentors (name, batch, company, linkedin, email)
            VALUES (?, ?, ?, ?, ?)
        """
        mentors = [
            ("Nisha Verma", "Batch of 2021", "Microsoft", "https://www.linkedin.com/in/", "nisha.verma@alumni.edu"),
            ("Rahul Iyer", "Batch of 2020", "Zoho", "https://www.linkedin.com/in/", "rahul.iyer@alumni.edu"),
            ("Sana Khan", "Batch of 2019", "Deloitte", "https://www.linkedin.com/in/", "sana.khan@alumni.edu"),
            ("Arjun Menon", "Batch of 2022", "Amazon", "https://www.linkedin.com/in/", "arjun.menon@alumni.edu"),
        ]
        for mentor in mentors:
            execute_query(app, seed_query, mentor)


def get_all_alumni_mentors(app):
    ensure_alumni_mentors_table(app)
    return fetch_all(app, "SELECT * FROM alumni_mentors ORDER BY id ASC")


def add_alumni_mentor(app, mentor_data):
    ensure_alumni_mentors_table(app)
    query = """
        INSERT INTO alumni_mentors (name, batch, company, linkedin, email)
        VALUES (?, ?, ?, ?, ?)
    """
    execute_query(
        app,
        query,
        (
            mentor_data["name"],
            mentor_data["batch"],
            mentor_data["company"],
            mentor_data["linkedin"],
            mentor_data["email"],
        ),
    )


def update_alumni_mentor(app, mentor_id, mentor_data):
    ensure_alumni_mentors_table(app)
    query = """
        UPDATE alumni_mentors
        SET name = ?, batch = ?, company = ?, linkedin = ?, email = ?
        WHERE id = ?
    """
    execute_query(
        app,
        query,
        (
            mentor_data["name"],
            mentor_data["batch"],
            mentor_data["company"],
            mentor_data["linkedin"],
            mentor_data["email"],
            mentor_id,
        ),
    )


def delete_alumni_mentor(app, mentor_id):
    ensure_alumni_mentors_table(app)
    execute_query(app, "DELETE FROM alumni_mentors WHERE id = ?", (mentor_id,))


def create_student(app, name, email, password, cgpa, roll_number, department, passout_year=None):
    ensure_users_table(app)
    password_hash = generate_password_hash(password)
    query = """
        INSERT INTO users (name, email, password_hash, role, cgpa, roll_number, department, passout_year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    return execute_query(app, query, (name, email, password_hash, "student", cgpa, roll_number, department, passout_year))


def create_officer(app, name, email, password, department="Placement Cell"):
    ensure_users_table(app)
    password_hash = generate_password_hash(password)
    query = """
        INSERT INTO users (name, email, password_hash, role, cgpa, roll_number, department, passout_year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    return execute_query(app, query, (name, email, password_hash, "officer", None, None, department, None))


def get_all_officers(app):
    ensure_users_table(app)
    return fetch_all(
        app,
        """
        SELECT id, name, email, department, created_at
        FROM users
        WHERE role = 'officer'
        ORDER BY created_at ASC, name ASC
        """,
    )


def email_exists(app, email, exclude_user_id=None):
    ensure_users_table(app)
    query = "SELECT id FROM users WHERE email = ?"
    params = [email]
    if exclude_user_id:
        query += " AND id <> ?"
        params.append(exclude_user_id)
    return fetch_one(app, query, params) is not None


def roll_number_exists(app, roll_number, exclude_user_id=None):
    ensure_users_table(app)
    query = "SELECT id FROM users WHERE roll_number = ?"
    params = [roll_number]
    if exclude_user_id:
        query += " AND id <> ?"
        params.append(exclude_user_id)
    return fetch_one(app, query, params) is not None


def get_user_by_email(app, email):
    ensure_users_table(app)
    record = fetch_one(app, "SELECT * FROM users WHERE email = ?", (email,))
    return User(record) if record else None


def get_user_by_id(app, user_id):
    ensure_users_table(app)
    record = fetch_one(app, "SELECT * FROM users WHERE id = ?", (user_id,))
    return User(record) if record else None


def verify_user(app, email, password):
    user = get_user_by_email(app, email)
    if user and check_password_hash(user.password_hash, password):
        return user
    return None


def update_user_profile(app, user_id, name, email, cgpa, roll_number, department, passout_year=None, update_passout_year=False):
    ensure_users_table(app)
    if update_passout_year:
        query = """
            UPDATE users
            SET name = ?, email = ?, cgpa = ?, roll_number = ?, department = ?, passout_year = ?
            WHERE id = ?
        """
        execute_query(app, query, (name, email, cgpa, roll_number, department, passout_year, user_id))
    else:
        query = """
            UPDATE users
            SET name = ?, email = ?, cgpa = ?, roll_number = ?, department = ?
            WHERE id = ?
        """
        execute_query(app, query, (name, email, cgpa, roll_number, department, user_id))


def update_officer_profile(app, user_id, name, email):
    ensure_users_table(app)
    query = """
        UPDATE users
        SET name = ?, email = ?
        WHERE id = ?
    """
    execute_query(app, query, (name, email, user_id))


def update_user_password(app, user_id, password):
    ensure_users_table(app)
    query = "UPDATE users SET password_hash = ? WHERE id = ?"
    execute_query(app, query, (generate_password_hash(password), user_id))


def delete_user(app, user_id):
    ensure_users_table(app)
    execute_query(app, "DELETE FROM users WHERE id = ?", (user_id,))


def get_student_skill_record(app, user_id):
    ensure_skills_table(app)
    record = fetch_one(
        app,
        """
        SELECT
            user_id,
            python,
            sql,
            java,
            dsa,
            communication,
            problem_solving,
            web_dev,
            ml,
            updated_at
        FROM skills
        WHERE user_id = ?
        """,
        (user_id,),
    )
    if record:
        return record
    return {field: 0 for field in SKILL_FIELDS} | {"user_id": user_id, "updated_at": None}


def upsert_student_skills(app, user_id, skill_values):
    ensure_skills_table(app)
    existing = fetch_one(app, "SELECT user_id FROM skills WHERE user_id = ?", (user_id,))

    if existing:
        query = """
            UPDATE skills
            SET python = ?, sql = ?, java = ?, dsa = ?, communication = ?,
                problem_solving = ?, web_dev = ?, ml = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """
        execute_query(
            app,
            query,
            (
                skill_values["python"],
                skill_values["sql"],
                skill_values["java"],
                skill_values["dsa"],
                skill_values["communication"],
                skill_values["problem_solving"],
                skill_values["web_dev"],
                skill_values["ml"],
                user_id,
            ),
        )
    else:
        query = """
            INSERT INTO skills (
                user_id, python, sql, java, dsa, communication, problem_solving, web_dev, ml
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        execute_query(
            app,
            query,
            (
                user_id,
                skill_values["python"],
                skill_values["sql"],
                skill_values["java"],
                skill_values["dsa"],
                skill_values["communication"],
                skill_values["problem_solving"],
                skill_values["web_dev"],
                skill_values["ml"],
            ),
        )


def get_all_companies(app, search_term=None, limit=None, offset=0):
    ensure_companies_table(app)
    query = "SELECT * FROM companies"
    params = []
    if search_term:
        query += " WHERE name LIKE ? OR role LIKE ? OR skills_required LIKE ?"
        search_like = f"%{search_term}%"
        params.extend([search_like, search_like, search_like])
    query += " ORDER BY drive_date ASC, name ASC"
    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
    return fetch_all(app, query, params)


def count_companies(app, search_term=None):
    ensure_companies_table(app)
    query = "SELECT COUNT(*) AS total FROM companies"
    params = []
    if search_term:
        query += " WHERE name LIKE ? OR role LIKE ? OR skills_required LIKE ?"
        search_like = f"%{search_term}%"
        params.extend([search_like, search_like, search_like])
    row = fetch_one(app, query, params)
    return row["total"] if row else 0


def get_company_by_id(app, company_id):
    ensure_companies_table(app)
    return fetch_one(app, "SELECT * FROM companies WHERE id = ?", (company_id,))


def add_company(app, company_data):
    ensure_companies_table(app)
    query = """
        INSERT INTO companies (name, role, ctc_lpa, min_cgpa, skills_required, drive_date, prep_kit_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    execute_query(
        app,
        query,
        (
            company_data["name"],
            company_data["role"],
            company_data["ctc_lpa"],
            company_data["min_cgpa"],
            company_data["skills_required"],
            company_data["drive_date"],
            company_data["prep_kit_url"],
        ),
    )


def update_company(app, company_id, company_data):
    ensure_companies_table(app)
    query = """
        UPDATE companies
        SET name = ?, role = ?, ctc_lpa = ?, min_cgpa = ?, skills_required = ?, drive_date = ?, prep_kit_url = ?
        WHERE id = ?
    """
    execute_query(
        app,
        query,
        (
            company_data["name"],
            company_data["role"],
            company_data["ctc_lpa"],
            company_data["min_cgpa"],
            company_data["skills_required"],
            company_data["drive_date"],
            company_data["prep_kit_url"],
            company_id,
        ),
    )


def delete_company(app, company_id):
    ensure_companies_table(app)
    execute_query(app, "DELETE FROM companies WHERE id = ?", (company_id,))


def get_students_with_skill_average(
    app,
    department=None,
    min_cgpa=None,
    search_term=None,
    skill_name=None,
    min_skill_score=None,
    passout_year=None,
    limit=None,
    offset=0,
):
    ensure_users_table(app)
    ensure_skills_table(app)

    conditions = ["u.role = 'student'"]
    params = []
    if department:
        conditions.append("u.department = ?")
        params.append(department)
    if min_cgpa not in (None, ""):
        conditions.append("u.cgpa >= ?")
        params.append(min_cgpa)
    if search_term:
        conditions.append("(u.name LIKE ? OR u.roll_number LIKE ? OR u.email LIKE ?)")
        search_like = f"%{search_term}%"
        params.extend([search_like, search_like, search_like])
    if skill_name and skill_name in SKILL_FIELDS:
        if min_skill_score not in (None, ""):
            conditions.append(f"COALESCE(s.{skill_name}, 0) >= ?")
            params.append(min_skill_score)
        else:
            conditions.append(f"COALESCE(s.{skill_name}, 0) > 0")
    if passout_year:
        conditions.append("u.passout_year = ?")
        params.append(passout_year)

    query = f"""
        SELECT
            u.id,
            u.name,
            u.email,
            u.roll_number,
            u.department,
            u.passout_year,
            u.cgpa,
            COALESCE(s.python, 0) AS python,
            COALESCE(s.sql, 0) AS sql,
            COALESCE(s.java, 0) AS java,
            COALESCE(s.dsa, 0) AS dsa,
            COALESCE(s.communication, 0) AS communication,
            COALESCE(s.problem_solving, 0) AS problem_solving,
            COALESCE(s.web_dev, 0) AS web_dev,
            COALESCE(s.ml, 0) AS ml,
            ROUND((
                COALESCE(s.python, 0) +
                COALESCE(s.sql, 0) +
                COALESCE(s.java, 0) +
                COALESCE(s.dsa, 0) +
                COALESCE(s.communication, 0) +
                COALESCE(s.problem_solving, 0) +
                COALESCE(s.web_dev, 0) +
                COALESCE(s.ml, 0)
            ) / 8.0, 2) AS skill_avg
        FROM users u
        LEFT JOIN skills s ON s.user_id = u.id
        WHERE {' AND '.join(conditions)}
        ORDER BY u.cgpa DESC, u.name ASC
    """
    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
    return fetch_all(app, query, params)


def count_students(
    app,
    department=None,
    min_cgpa=None,
    search_term=None,
    skill_name=None,
    min_skill_score=None,
    passout_year=None,
):
    ensure_users_table(app)
    ensure_skills_table(app)

    conditions = ["u.role = 'student'"]
    params = []
    if department:
        conditions.append("u.department = ?")
        params.append(department)
    if min_cgpa not in (None, ""):
        conditions.append("u.cgpa >= ?")
        params.append(min_cgpa)
    if search_term:
        conditions.append("(u.name LIKE ? OR u.roll_number LIKE ? OR u.email LIKE ?)")
        search_like = f"%{search_term}%"
        params.extend([search_like, search_like, search_like])
    if skill_name and skill_name in SKILL_FIELDS:
        if min_skill_score not in (None, ""):
            conditions.append(f"COALESCE(s.{skill_name}, 0) >= ?")
            params.append(min_skill_score)
        else:
            conditions.append(f"COALESCE(s.{skill_name}, 0) > 0")
    if passout_year:
        conditions.append("u.passout_year = ?")
        params.append(passout_year)

    row = fetch_one(
        app,
        f"SELECT COUNT(*) AS total FROM users u LEFT JOIN skills s ON s.user_id = u.id WHERE {' AND '.join(conditions)}",
        params,
    )
    return row["total"] if row else 0


def get_departments(app):
    ensure_users_table(app)
    rows = fetch_all(
        app,
        """
        SELECT DISTINCT department
        FROM users
        WHERE role = 'student' AND department IS NOT NULL AND department <> ''
        ORDER BY department
        """,
    )
    return [row["department"] for row in rows]


def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
