from functools import wraps

import pymysql
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


class User(UserMixin):
    def __init__(self, record):
        self.id = record["id"]
        self.name = record["name"]
        self.email = record["email"]
        self.password_hash = record["password_hash"]
        self.role = record["role"]
        self.cgpa = record["cgpa"]
        self.roll_number = record["roll_number"]
        self.department = record["department"]
        self.created_at = record["created_at"]


def get_connection(app):
    return pymysql.connect(
        host=app.config["DB_HOST"],
        port=app.config["DB_PORT"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"],
        database=app.config["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def fetch_one(app, query, params=None):
    with get_connection(app) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()


def fetch_all(app, query, params=None):
    with get_connection(app) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()


def execute_query(app, query, params=None):
    with get_connection(app) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.lastrowid


def ensure_contact_settings_table(app):
    create_query = """
        CREATE TABLE IF NOT EXISTS contact_settings (
            id INT PRIMARY KEY,
            map_embed_url VARCHAR(500) NOT NULL,
            office_address VARCHAR(255) NOT NULL,
            phone VARCHAR(50) NOT NULL,
            email VARCHAR(150) NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """
    seed_query = """
        INSERT INTO contact_settings (id, map_embed_url, office_address, phone, email)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE id = id
    """
    execute_query(app, create_query)
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


def get_contact_settings(app):
    ensure_contact_settings_table(app)
    return fetch_one(app, "SELECT * FROM contact_settings WHERE id = 1")


def update_contact_settings(app, map_embed_url, office_address, phone, email):
    ensure_contact_settings_table(app)
    query = """
        UPDATE contact_settings
        SET map_embed_url = %s, office_address = %s, phone = %s, email = %s
        WHERE id = 1
    """
    execute_query(app, query, (map_embed_url, office_address, phone, email))


def ensure_alumni_mentors_table(app):
    create_query = """
        CREATE TABLE IF NOT EXISTS alumni_mentors (
            id INT AUTO_INCREMENT PRIMARY KEY,
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
            VALUES (%s, %s, %s, %s, %s)
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
        VALUES (%s, %s, %s, %s, %s)
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
        SET name = %s, batch = %s, company = %s, linkedin = %s, email = %s
        WHERE id = %s
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
    execute_query(app, "DELETE FROM alumni_mentors WHERE id = %s", (mentor_id,))


def create_student(app, name, email, password, cgpa, roll_number, department):
    password_hash = generate_password_hash(password)
    query = """
        INSERT INTO users (name, email, password_hash, role, cgpa, roll_number, department)
        VALUES (%s, %s, %s, 'student', %s, %s, %s)
    """
    return execute_query(app, query, (name, email, password_hash, cgpa, roll_number, department))


def create_officer(app, name, email, password, department="Placement Cell"):
    password_hash = generate_password_hash(password)
    query = """
        INSERT INTO users (name, email, password_hash, role, cgpa, roll_number, department)
        VALUES (%s, %s, %s, 'officer', NULL, NULL, %s)
    """
    return execute_query(app, query, (name, email, password_hash, department))


def get_all_officers(app):
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
    query = "SELECT id FROM users WHERE email = %s"
    params = [email]
    if exclude_user_id:
        query += " AND id <> %s"
        params.append(exclude_user_id)
    return fetch_one(app, query, params) is not None


def roll_number_exists(app, roll_number, exclude_user_id=None):
    query = "SELECT id FROM users WHERE roll_number = %s"
    params = [roll_number]
    if exclude_user_id:
        query += " AND id <> %s"
        params.append(exclude_user_id)
    return fetch_one(app, query, params) is not None


def get_user_by_email(app, email):
    record = fetch_one(app, "SELECT * FROM users WHERE email = %s", (email,))
    return User(record) if record else None


def get_user_by_id(app, user_id):
    record = fetch_one(app, "SELECT * FROM users WHERE id = %s", (user_id,))
    return User(record) if record else None


def verify_user(app, email, password):
    user = get_user_by_email(app, email)
    if user and check_password_hash(user.password_hash, password):
        return user
    return None


def update_user_profile(app, user_id, name, email, cgpa, roll_number, department):
    query = """
        UPDATE users
        SET name = %s, email = %s, cgpa = %s, roll_number = %s, department = %s
        WHERE id = %s
    """
    execute_query(app, query, (name, email, cgpa, roll_number, department, user_id))


def update_officer_profile(app, user_id, name, email):
    query = """
        UPDATE users
        SET name = %s, email = %s
        WHERE id = %s
    """
    execute_query(app, query, (name, email, user_id))


def update_user_password(app, user_id, password):
    query = "UPDATE users SET password_hash = %s WHERE id = %s"
    execute_query(app, query, (generate_password_hash(password), user_id))


def delete_user(app, user_id):
    execute_query(app, "DELETE FROM users WHERE id = %s", (user_id,))


def get_student_skill_record(app, user_id):
    record = fetch_one(
        app,
        """
        SELECT
            user_id,
            python,
            `sql` AS sql_rating,
            java,
            dsa,
            communication,
            problem_solving,
            web_dev,
            ml,
            updated_at
        FROM skills
        WHERE user_id = %s
        """,
        (user_id,),
    )
    if record:
        record["sql"] = record.pop("sql_rating")
        return record
    return {field: 1 for field in SKILL_FIELDS} | {"user_id": user_id, "updated_at": None}


def upsert_student_skills(app, user_id, skill_values):
    query = """
        INSERT INTO skills (
            user_id, python, `sql`, java, dsa, communication, problem_solving, web_dev, ml
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            python = VALUES(python),
            `sql` = VALUES(`sql`),
            java = VALUES(java),
            dsa = VALUES(dsa),
            communication = VALUES(communication),
            problem_solving = VALUES(problem_solving),
            web_dev = VALUES(web_dev),
            ml = VALUES(ml)
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
    query = "SELECT * FROM companies"
    params = []
    if search_term:
        query += " WHERE name LIKE %s OR role LIKE %s OR skills_required LIKE %s"
        search_like = f"%{search_term}%"
        params.extend([search_like, search_like, search_like])
    query += " ORDER BY drive_date ASC, name ASC"
    if limit is not None:
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
    return fetch_all(app, query, params)


def count_companies(app, search_term=None):
    query = "SELECT COUNT(*) AS total FROM companies"
    params = []
    if search_term:
        query += " WHERE name LIKE %s OR role LIKE %s OR skills_required LIKE %s"
        search_like = f"%{search_term}%"
        params.extend([search_like, search_like, search_like])
    row = fetch_one(app, query, params)
    return row["total"] if row else 0


def get_company_by_id(app, company_id):
    return fetch_one(app, "SELECT * FROM companies WHERE id = %s", (company_id,))


def add_company(app, company_data):
    query = """
        INSERT INTO companies (name, role, ctc_lpa, min_cgpa, skills_required, drive_date, prep_kit_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
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
    query = """
        UPDATE companies
        SET name = %s, role = %s, ctc_lpa = %s, min_cgpa = %s, skills_required = %s, drive_date = %s, prep_kit_url = %s
        WHERE id = %s
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
    execute_query(app, "DELETE FROM companies WHERE id = %s", (company_id,))


def get_students_with_skill_average(app, department=None, min_cgpa=None, search_term=None, limit=None, offset=0):
    conditions = ["u.role = 'student'"]
    params = []
    if department:
        conditions.append("u.department = %s")
        params.append(department)
    if min_cgpa not in (None, ""):
        conditions.append("u.cgpa >= %s")
        params.append(min_cgpa)
    if search_term:
        conditions.append("(u.name LIKE %s OR u.roll_number LIKE %s OR u.email LIKE %s)")
        search_like = f"%{search_term}%"
        params.extend([search_like, search_like, search_like])

    query = f"""
        SELECT
            u.id,
            u.name,
            u.email,
            u.roll_number,
            u.department,
            u.cgpa,
            ROUND((
                COALESCE(s.python, 0) +
                COALESCE(s.`sql`, 0) +
                COALESCE(s.java, 0) +
                COALESCE(s.dsa, 0) +
                COALESCE(s.communication, 0) +
                COALESCE(s.problem_solving, 0) +
                COALESCE(s.web_dev, 0) +
                COALESCE(s.ml, 0)
            ) / 8, 2) AS skill_avg
        FROM users u
        LEFT JOIN skills s ON s.user_id = u.id
        WHERE {' AND '.join(conditions)}
        ORDER BY u.cgpa DESC, u.name ASC
    """
    if limit is not None:
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
    return fetch_all(app, query, params)


def count_students(app, department=None, min_cgpa=None, search_term=None):
    conditions = ["role = 'student'"]
    params = []
    if department:
        conditions.append("department = %s")
        params.append(department)
    if min_cgpa not in (None, ""):
        conditions.append("cgpa >= %s")
        params.append(min_cgpa)
    if search_term:
        conditions.append("(name LIKE %s OR roll_number LIKE %s OR email LIKE %s)")
        search_like = f"%{search_term}%"
        params.extend([search_like, search_like, search_like])

    row = fetch_one(app, f"SELECT COUNT(*) AS total FROM users WHERE {' AND '.join(conditions)}", params)
    return row["total"] if row else 0


def get_departments(app):
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
