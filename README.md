# SkillRadar

SkillRadar is a Flask + MySQL web application for smart campus placement tracking, skill self-assessment, radar chart benchmarking, and officer-side eligibility monitoring.

## Run Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up MySQL:
   ```sql
   CREATE DATABASE smart_campus;
   ```
   Then run `schema.sql` against that database.

3. Edit database credentials in `config.py` or provide them through environment variables:
   - `DB_HOST`
   - `DB_PORT`
   - `DB_USER`
   - `DB_PASSWORD`
   - `DB_NAME`
   - `SECRET_KEY`

4. Start the app:
   ```bash
   flask --app app run
   ```

5. Test logins:
   - Officer: `officer@campus.edu` / `admin123`
   - Student: `student1@campus.edu` / `pass123`
   - Student: `student2@campus.edu` / `pass123`

## Notes

- The app uses Flask-Login with role-based access for students and placement officers.
- Students can register, save skills, visualize skill gaps, browse companies, and contact mentors.
- Officers can view all students, filter eligibility, and add new company drives from the placement hub.
