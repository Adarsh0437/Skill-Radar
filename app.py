import csv
from datetime import datetime
from io import StringIO

from flask import Flask, Response, jsonify, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

from config import Config
from models import (
    SKILL_FIELDS,
    add_company,
    add_alumni_mentor,
    count_companies,
    count_students,
    create_officer,
    create_student,
    delete_alumni_mentor,
    delete_company,
    delete_user,
    email_exists,
    get_all_companies,
    get_all_alumni_mentors,
    get_all_officers,
    get_company_by_id,
    get_contact_settings,
    get_departments,
    get_student_skill_record,
    get_students_with_skill_average,
    get_user_by_email,
    get_user_by_id,
    role_required,
    roll_number_exists,
    update_alumni_mentor,
    update_company,
    update_contact_settings,
    update_officer_profile,
    update_user_password,
    update_user_profile,
    upsert_student_skills,
    verify_user,
)

INDUSTRY_STANDARDS = {
    "python": 8,
    "sql": 7,
    "java": 7,
    "dsa": 8,
    "communication": 8,
    "problem_solving": 8,
    "web_dev": 6,
    "ml": 6,
}

SKILL_LABELS = {
    "python": "Python",
    "sql": "SQL",
    "java": "Java",
    "dsa": "DSA",
    "communication": "Communication",
    "problem_solving": "Problem Solving",
    "web_dev": "Web Dev",
    "ml": "Machine Learning",
}

def calculate_gap(student_skills, industry_standards):
    per_skill_gap = {}
    total_gap = 0
    total_industry = sum(industry_standards.values())
    for skill, benchmark in industry_standards.items():
        student_score = int(student_skills.get(skill, 0))
        gap = max(0, benchmark - student_score)
        per_skill_gap[skill] = gap
        total_gap += gap

    overall_gap = round((total_gap / total_industry) * 100, 2) if total_industry else 0
    weakest = sorted(per_skill_gap.items(), key=lambda item: item[1], reverse=True)
    top_focus = [SKILL_LABELS[skill] for skill, gap in weakest if gap > 0][:3]
    return per_skill_gap, overall_gap, top_focus


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    STUDENTS_PER_PAGE = 6
    COMPANIES_PER_PAGE = 6

    def parse_cgpa(raw_value):
        try:
            cgpa = round(float(raw_value), 2)
            if cgpa < 0 or cgpa > 10:
                raise ValueError
            return cgpa
        except ValueError as exc:
            raise ValueError("CGPA must be a number between 0 and 10.") from exc

    def parse_page(raw_value):
        try:
            page = int(raw_value)
            return page if page > 0 else 1
        except (TypeError, ValueError):
            return 1

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return get_user_by_id(app, user_id)

    @app.context_processor
    def inject_globals():
        return {"current_year": datetime.now().year}

    @app.route("/")
    def home():
        if current_user.is_authenticated:
            return redirect(url_for("officer_panel" if current_user.role == "officer" else "dashboard"))
        return redirect(url_for("login"))

    def handle_login(expected_role=None):
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = verify_user(app, email, password)
            if user:
                if expected_role and user.role != expected_role:
                    flash(f"This login is only for {expected_role}s. Please use the correct portal.", "danger")
                    return False
                login_user(user)
                flash("Welcome back to SkillRadar.", "success")
                return redirect(url_for("officer_panel" if user.role == "officer" else "dashboard"))
            flash("Invalid email or password.", "danger")
        return None

    @app.route("/login")
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        return render_template("login.html", login_mode="hub")

    @app.route("/login/student", methods=["GET", "POST"])
    def student_login():
        login_result = handle_login("student")
        if login_result:
            return login_result

        return render_template("login.html", login_mode="student")

    @app.route("/login/officer", methods=["GET", "POST"])
    def officer_login():
        login_result = handle_login("officer")
        if login_result:
            return login_result

        return render_template("login.html", login_mode="officer")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        form = {key: request.form.get(key, "").strip() for key in ["name", "email", "cgpa", "roll_number", "department"]}
        if request.method == "POST":
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not all(form.values()) or not password or not confirm_password:
                flash("Please complete all registration fields.", "danger")
                return render_template("register.html", form=form)

            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return render_template("register.html", form=form)

            if get_user_by_email(app, form["email"].lower()):
                flash("An account with this email already exists.", "danger")
                return render_template("register.html", form=form)

            try:
                cgpa = parse_cgpa(form["cgpa"])
            except ValueError as error:
                flash(str(error), "danger")
                return render_template("register.html", form=form)

            create_student(app, form["name"], form["email"].lower(), password, cgpa, form["roll_number"], form["department"])
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("student_login"))

        return render_template("register.html", form=form)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been signed out.", "info")
        return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    @role_required("student")
    def dashboard():
        skills = get_student_skill_record(app, current_user.id)
        saved_scores = [int(skills[field]) for field in SKILL_FIELDS]
        has_skill_profile = skills.get("updated_at") is not None
        completion = round((sum(1 for score in saved_scores if score > 1) / len(SKILL_FIELDS)) * 100)
        skill_avg = round(sum(saved_scores) / len(saved_scores), 2) if has_skill_profile else None
        if has_skill_profile:
            _, overall_gap, top_focus = calculate_gap(skills, INDUSTRY_STANDARDS)
        else:
            overall_gap = None
            top_focus = []
        return render_template(
            "dashboard.html",
            skills=skills,
            skill_avg=skill_avg,
            completion=completion,
            overall_gap=overall_gap,
            top_focus=top_focus,
            has_skill_profile=has_skill_profile,
        )

    @app.route("/student/profile", methods=["POST"])
    @login_required
    @role_required("student")
    def update_student_profile():
        form = {key: request.form.get(key, "").strip() for key in ["name", "email", "cgpa", "roll_number", "department"]}
        password = request.form.get("password", "").strip()

        if not all(form.values()):
            flash("Please complete all student profile fields.", "danger")
            return redirect(url_for("dashboard"))

        if email_exists(app, form["email"].lower(), current_user.id):
            flash("That email is already used by another account.", "danger")
            return redirect(url_for("dashboard"))

        if roll_number_exists(app, form["roll_number"], current_user.id):
            flash("That roll number is already used by another student.", "danger")
            return redirect(url_for("dashboard"))

        try:
            cgpa = parse_cgpa(form["cgpa"])
        except ValueError as error:
            flash(str(error), "danger")
            return redirect(url_for("dashboard"))

        update_user_profile(app, current_user.id, form["name"], form["email"].lower(), cgpa, form["roll_number"], form["department"])
        if password:
            update_user_password(app, current_user.id, password)
        flash("Student profile updated successfully.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/student/delete", methods=["POST"])
    @login_required
    @role_required("student")
    def delete_student_account():
        user_id = current_user.id
        logout_user()
        delete_user(app, user_id)
        flash("Your student account has been deleted.", "info")
        return redirect(url_for("student_login"))

    @app.route("/skill_form", methods=["GET", "POST"])
    @login_required
    @role_required("student")
    def skill_form():
        if request.method == "POST":
            skill_values = {}
            try:
                for field in SKILL_FIELDS:
                    value = int(request.form.get(field, 1))
                    if value < 1 or value > 10:
                        raise ValueError
                    skill_values[field] = value
            except ValueError:
                flash("Each skill rating must be between 1 and 10.", "danger")
                return redirect(url_for("skill_form"))

            upsert_student_skills(app, current_user.id, skill_values)
            flash("Your skill profile has been saved.", "success")
            return redirect(url_for("skill_form"))

        skills = get_student_skill_record(app, current_user.id)
        return render_template("skill_form.html", skills=skills, skill_labels=SKILL_LABELS)

    @app.route("/visualize")
    @login_required
    @role_required("student")
    def visualize():
        skills = get_student_skill_record(app, current_user.id)
        if skills.get("updated_at") is None:
            flash("Complete your skill form first to unlock the radar chart and gap analysis.", "info")
            return redirect(url_for("skill_form"))
        per_skill_gap, overall_gap, top_focus = calculate_gap(skills, INDUSTRY_STANDARDS)
        student_chart = [int(skills[field]) for field in SKILL_FIELDS]
        industry_chart = [INDUSTRY_STANDARDS[field] for field in SKILL_FIELDS]
        pretty_labels = [SKILL_LABELS[field] for field in SKILL_FIELDS]
        return render_template(
            "visualize.html",
            skill_fields=SKILL_FIELDS,
            skill_labels=SKILL_LABELS,
            pretty_labels=pretty_labels,
            student_chart=student_chart,
            industry_chart=industry_chart,
            per_skill_gap=per_skill_gap,
            overall_gap=overall_gap,
            top_focus=top_focus,
        )

    @app.route("/placement_hub", methods=["GET", "POST"])
    @login_required
    def placement_hub():
        if request.method == "POST":
            if current_user.role != "officer":
                return redirect(url_for("placement_hub"))

            form = {key: request.form.get(key, "").strip() for key in ["name", "role", "ctc_lpa", "min_cgpa", "skills_required", "drive_date", "prep_kit_url"]}
            if not all(form.values()):
                flash("Please fill all company fields.", "danger")
            else:
                add_company(app, form)
                flash("Company added successfully.", "success")
            return redirect(url_for("placement_hub"))

        company_search = request.args.get("q", "").strip()
        page = parse_page(request.args.get("page", 1))
        total_companies = count_companies(app, company_search or None)
        total_pages = max(1, (total_companies + COMPANIES_PER_PAGE - 1) // COMPANIES_PER_PAGE)
        page = min(page, total_pages)
        offset = (page - 1) * COMPANIES_PER_PAGE
        companies = get_all_companies(app, company_search or None, COMPANIES_PER_PAGE, offset)
        return render_template(
            "placement_hub.html",
            companies=companies,
            company_search=company_search,
            company_page=page,
            company_total_pages=total_pages,
        )

    @app.route("/company/<int:company_id>/update", methods=["POST"])
    @login_required
    @role_required("officer")
    def update_company_route(company_id):
        if not get_company_by_id(app, company_id):
            flash("Company record not found.", "danger")
            return redirect(url_for("placement_hub"))

        form = {key: request.form.get(key, "").strip() for key in ["name", "role", "ctc_lpa", "min_cgpa", "skills_required", "drive_date", "prep_kit_url"]}
        if not all(form.values()):
            flash("Please complete all company fields before updating.", "danger")
            return redirect(url_for("placement_hub"))

        update_company(app, company_id, form)
        flash("Company updated successfully.", "success")
        return redirect(url_for("placement_hub"))

    @app.route("/company/<int:company_id>/delete", methods=["POST"])
    @login_required
    @role_required("officer")
    def delete_company_route(company_id):
        delete_company(app, company_id)
        flash("Company deleted successfully.", "info")
        return redirect(url_for("placement_hub"))

    @app.route("/contact")
    @login_required
    def contact():
        return render_template("contact.html", mentors=get_all_alumni_mentors(app), contact_settings=get_contact_settings(app))

    @app.route("/contact/update", methods=["POST"])
    @login_required
    @role_required("officer")
    def update_contact_page_settings():
        map_embed_url = request.form.get("map_embed_url", "").strip()
        office_address = request.form.get("office_address", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip().lower()

        if not all([map_embed_url, office_address, phone, email]):
            flash("Please complete all contact settings fields.", "danger")
            return redirect(url_for("contact"))

        update_contact_settings(app, map_embed_url, office_address, phone, email)
        flash("Contact page settings updated successfully.", "success")
        return redirect(url_for("contact"))

    @app.route("/mentor/add", methods=["POST"])
    @login_required
    @role_required("officer")
    def add_mentor():
        form = {key: request.form.get(key, "").strip() for key in ["name", "batch", "company", "linkedin", "email"]}
        if not all(form.values()):
            flash("Please complete all mentor fields before adding.", "danger")
            return redirect(url_for("contact"))

        add_alumni_mentor(app, form)
        flash("Mentor added successfully.", "success")
        return redirect(url_for("contact"))

    @app.route("/mentor/<int:mentor_id>/update", methods=["POST"])
    @login_required
    @role_required("officer")
    def update_mentor(mentor_id):
        form = {key: request.form.get(key, "").strip() for key in ["name", "batch", "company", "linkedin", "email"]}
        if not all(form.values()):
            flash("Please complete all mentor fields before updating.", "danger")
            return redirect(url_for("contact"))

        update_alumni_mentor(app, mentor_id, form)
        flash("Mentor updated successfully.", "success")
        return redirect(url_for("contact"))

    @app.route("/mentor/<int:mentor_id>/delete", methods=["POST"])
    @login_required
    @role_required("officer")
    def delete_mentor(mentor_id):
        delete_alumni_mentor(app, mentor_id)
        flash("Mentor deleted successfully.", "info")
        return redirect(url_for("contact"))

    @app.route("/officer_panel")
    @login_required
    @role_required("officer")
    def officer_panel():
        department = request.args.get("department", "").strip()
        min_cgpa = request.args.get("min_cgpa", "").strip()
        student_search = request.args.get("q", "").strip()
        page = parse_page(request.args.get("page", 1))
        total_students = count_students(app, department or None, min_cgpa or None, student_search or None)
        total_pages = max(1, (total_students + STUDENTS_PER_PAGE - 1) // STUDENTS_PER_PAGE)
        page = min(page, total_pages)
        offset = (page - 1) * STUDENTS_PER_PAGE
        students = get_students_with_skill_average(app, department or None, min_cgpa or None, student_search or None, STUDENTS_PER_PAGE, offset)
        return render_template(
            "officer_panel.html",
            students=students,
            officers=get_all_officers(app),
            departments=get_departments(app),
            selected_department=department,
            min_cgpa=min_cgpa,
            student_search=student_search,
            student_page=page,
            student_total_pages=total_pages,
        )

    @app.route("/officer_panel/export")
    @login_required
    @role_required("officer")
    def export_officer_csv():
        department = request.args.get("department", "").strip()
        min_cgpa = request.args.get("min_cgpa", "").strip()
        student_search = request.args.get("q", "").strip()
        students = get_students_with_skill_average(app, department or None, min_cgpa or None, student_search or None)

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "Email", "Roll Number", "Department", "CGPA", "Skill Avg Score"])
        for student in students:
            writer.writerow([
                student["name"],
                student["email"],
                student["roll_number"],
                student["department"],
                student["cgpa"],
                student["skill_avg"] or 0,
            ])

        filename = f"skillradar_students_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    @app.route("/officer/profile", methods=["POST"])
    @login_required
    @role_required("officer")
    def update_officer_details():
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not name or not email:
            flash("Officer name and email are required.", "danger")
            return redirect(url_for("officer_panel"))

        if email_exists(app, email, current_user.id):
            flash("That email is already used by another account.", "danger")
            return redirect(url_for("officer_panel"))

        update_officer_profile(app, current_user.id, name, email)
        if password:
            update_user_password(app, current_user.id, password)
        flash("Officer details updated successfully.", "success")
        return redirect(url_for("officer_panel"))

    @app.route("/officer/create", methods=["POST"])
    @login_required
    @role_required("officer")
    def create_officer_account():
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        department = request.form.get("department", "").strip() or "Placement Cell"

        if not name or not email or not password:
            flash("Name, email, and password are required to add a new officer.", "danger")
            return redirect(url_for("officer_panel"))

        if email_exists(app, email):
            flash("That email is already used by another account.", "danger")
            return redirect(url_for("officer_panel"))

        create_officer(app, name, email, password, department)
        flash("New officer account created successfully.", "success")
        return redirect(url_for("officer_panel"))

    @app.route("/officer/student/<int:user_id>/update", methods=["POST"])
    @login_required
    @role_required("officer")
    def officer_update_student(user_id):
        student = get_user_by_id(app, user_id)
        if not student or student.role != "student":
            flash("Student record not found.", "danger")
            return redirect(url_for("officer_panel"))

        form = {key: request.form.get(key, "").strip() for key in ["name", "email", "cgpa", "roll_number", "department"]}
        if not all(form.values()):
            flash("Please complete all student fields before updating.", "danger")
            return redirect(url_for("officer_panel"))

        if email_exists(app, form["email"].lower(), user_id):
            flash("That email is already used by another account.", "danger")
            return redirect(url_for("officer_panel"))

        if roll_number_exists(app, form["roll_number"], user_id):
            flash("That roll number is already used by another student.", "danger")
            return redirect(url_for("officer_panel"))

        try:
            cgpa = parse_cgpa(form["cgpa"])
        except ValueError as error:
            flash(str(error), "danger")
            return redirect(url_for("officer_panel"))

        update_user_profile(app, user_id, form["name"], form["email"].lower(), cgpa, form["roll_number"], form["department"])
        flash("Student record updated successfully.", "success")
        return redirect(url_for("officer_panel"))

    @app.route("/officer/student/<int:user_id>/delete", methods=["POST"])
    @login_required
    @role_required("officer")
    def officer_delete_student(user_id):
        student = get_user_by_id(app, user_id)
        if not student or student.role != "student":
            flash("Student record not found.", "danger")
            return redirect(url_for("officer_panel"))

        delete_user(app, user_id)
        flash("Student record deleted successfully.", "info")
        return redirect(url_for("officer_panel"))

    @app.route("/api/chart-data")
    @login_required
    @role_required("student")
    def chart_data():
        skills = get_student_skill_record(app, current_user.id)
        if skills.get("updated_at") is None:
            return jsonify({"error": "Skill profile not created yet."}), 400
        return jsonify({
            "labels": [SKILL_LABELS[field] for field in SKILL_FIELDS],
            "student": [int(skills[field]) for field in SKILL_FIELDS],
            "industry": [INDUSTRY_STANDARDS[field] for field in SKILL_FIELDS],
        })

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("base.html", error_message="You do not have access to this page."), 403

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
