# SkillRadar

Smart Campus Placement & Skill Analyzer built with Flask, Jinja2, vanilla JavaScript, Plotly, and a database layer that supports SQLite by default with optional PostgreSQL via `DATABASE_URL`.

`SkillRadar` helps students understand placement readiness through skill self-assessment and benchmark comparison, while giving placement officers a centralized platform to manage students, company drives, contact information, and alumni mentors.

Repository: [Adarsh0437/Skill-Radar](https://github.com/Adarsh0437/Skill-Radar)

## Overview

Campus placement preparation is often fragmented. Students may know their CGPA, but not how their technical and communication skills compare to placement expectations. Placement officers often manage eligibility, company data, and communication through scattered spreadsheets and manual updates.

SkillRadar brings those workflows into one web application.

Students can:
- register and manage their profile
- rate core placement skills on a `0-10` scale
- compare themselves with industry benchmark values
- view radar-chart based skill analysis
- check company eligibility
- access prep resources
- view placement contact and alumni mentor details

Placement officers can:
- monitor all registered students
- filter and search student records
- export filtered student data as CSV
- add, update, and delete company drives
- manage officer accounts
- update placement office contact information
- manage alumni mentor profiles

## Key Features

### Student Features
- Separate student login portal
- Student registration and secure login
- Profile update and account deletion
- Skill self-rating form on a `0-10` scale for:
  - Python
  - SQL
  - Java
  - DSA
  - Communication
  - Problem Solving
  - Web Development
  - Machine Learning
- Radar chart comparison between student skills and industry standards
- Skill gap percentage with suggested focus areas
- Placement hub with eligibility based on CGPA plus required skill thresholds

### Placement Officer Features
- Separate officer login portal
- Officer profile update
- Officer account creation from the officer panel
- Student management with:
  - department filter
  - minimum CGPA filter
  - search by name, roll number, or email
  - skill-based filtering
  - passout-year filtering
  - CSV export
- Student record update and delete actions
- Company add, update, delete, search, and pagination
- Editable placement office contact details
- Editable alumni mentor cards

### UI / Experience
- Dark academic theme with navy and gold palette
- Plotly radar chart visualization
- Premium card-based interface
- Active navigation highlighting
- Mobile-responsive layouts
- Custom themed dropdowns
- Modal-based mentor editing
- Inline form validation feedback

## Tech Stack

- Backend: Flask
- Authentication: Flask-Login
- Database:
  - SQLite by default for local development
  - optional PostgreSQL when `DATABASE_URL` is provided
- Frontend: HTML, CSS, Jinja2 templates, vanilla JavaScript
- Charts: Plotly.js
- Deployment:
  - Render with hosted PostgreSQL
  - PythonAnywhere with SQLite

## Project Structure

```text
Skill-Radar/
|-- app.py
|-- config.py
|-- models.py
|-- pythonanywhere_wsgi.py
|-- render.yaml
|-- requirements.txt
|-- schema.sql
|-- static/
|   |-- css/style.css
|   |-- img/skillradar-logo.svg
|   `-- js/chart.js
|-- templates/
|   |-- base.html
|   |-- contact.html
|   |-- dashboard.html
|   |-- login.html
|   |-- officer_panel.html
|   |-- placement_hub.html
|   |-- register.html
|   |-- skill_form.html
|   `-- visualize.html
`-- report_assets/
    |-- 01_home_portal.png
    |-- 02_register.png
    |-- 03_student_dashboard.png
    |-- 04_skill_form.png
    |-- 05_radar_chart.png
    |-- 06_placement_hub_student.png
    |-- 07_officer_panel.png
    `-- 08_contact.png
```

## How It Works

1. Students register with academic details such as name, email, CGPA, roll number, and department.
2. Students log in and submit self-ratings for the core placement skills tracked by the app.
3. The app compares student ratings with predefined industry benchmark scores.
4. A radar chart visually shows the difference between current skills and expected industry levels.
5. The placement hub checks company eligibility using student CGPA and required tracked skill thresholds from the company profile.
6. Officers can search, filter, export, and manage student and company records from the admin side.
7. Contact details and mentor information can be updated directly by officers through the UI.

## Skill Gap Logic

SkillRadar uses a simple benchmark comparison formula:

- Gap per skill = `max(0, industry_score - student_score)`
- Overall skill gap % = `(sum of gaps / sum of industry benchmark scores) * 100`

This helps students understand where improvement is needed most.

## Placement Eligibility Logic

Placement Hub eligibility is based on:

- `student.cgpa >= company.min_cgpa`
- if a company's `skills_required` text mentions tracked skills such as `Python`, `SQL`, `DSA`, or `Web Dev`, those required skills must each be at least `6/10`

This gives a more practical result than CGPA-only filtering while keeping company setup simple for officers.

## Real-World Use Case

SkillRadar is useful for college placement cells because it:
- helps students identify weak skill areas early
- reduces dependency on manual spreadsheets
- centralizes company and student placement data
- improves transparency in eligibility tracking
- gives officers better visibility into campus readiness

Example scenarios:
- A student may discover a strong CGPA but weak DSA and SQL ratings.
- A placement officer may filter students from a specific department above a CGPA cutoff for a drive.
- The placement cell can instantly update office contact information or mentor details without touching code.

## Screenshots

### Home / Portal
![Home / Portal](report_assets/01_home_portal.png)

### Student Registration
![Student Registration](report_assets/02_register.png)

### Student Dashboard
![Student Dashboard](report_assets/03_student_dashboard.png)

### Skill Form
![Skill Form](report_assets/04_skill_form.png)

### Radar Chart
![Radar Chart](report_assets/05_radar_chart.png)

### Placement Hub
![Placement Hub](report_assets/06_placement_hub_student.png)

### Officer Panel
![Officer Panel](report_assets/07_officer_panel.png)

### Contact Page
![Contact Page](report_assets/08_contact.png)

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Adarsh0437/Skill-Radar.git
cd Skill-Radar
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Copy `.env.example` to `.env` if you want to set custom values.

Example:

```env
SECRET_KEY=skillradar-dev-secret
DB_PATH=
DATABASE_URL=
```

Notes:
- leave `DATABASE_URL` empty for SQLite
- if `DB_PATH` is empty, the app defaults to `instance/skillradar.db`

### 5. Run the app

The app uses SQLite locally by default and creates the database automatically on first run.

```bash
flask --app app run
```

Open:

```text
http://127.0.0.1:5000
```

## Default Accounts

- Officer: `officer@campus.edu` / `admin123`
- Student 1: `student1@campus.edu` / `pass123`
- Student 2: `student2@campus.edu` / `pass123`

## Test Credentials

### Officer
- Email: `officer@campus.edu`
- Password: `admin123`

### Students
- Email: `student1@campus.edu`
- Password: `pass123`

- Email: `student2@campus.edu`
- Password: `pass123`

## Deploy on Render

Render is the primary cloud deployment path for this project. For reliable persistence on the free plan, use a hosted PostgreSQL database such as Neon or Supabase.

### 1. Push the project to GitHub

Make sure your latest code is in the repository Render will deploy from.

### 2. Create a hosted PostgreSQL database

Use either:
- Neon Postgres
- Supabase Postgres

Copy the connection string they provide. It will look like:

```text
postgresql://username:password@host/database?sslmode=require
```

### 3. Create a Render Web Service

- Choose `New +` -> `Web Service`
- Connect your GitHub repository
- Select the `Skill-Radar` repository

### 4. Use these Render settings

- Environment: `Python 3`
- Build command:

```bash
pip install -r requirements.txt
```

- Start command:

```bash
gunicorn app:app
```

### 5. Add environment variables

Set these in Render:

- `SECRET_KEY` = your own secret key
- `DATABASE_URL` = your hosted PostgreSQL connection string

### 6. Deploy

After the first deploy:
- the app will automatically create the schema
- default accounts will be seeded if they do not already exist
- future registrations and officer-created records will persist in PostgreSQL

### Render Notes

- local development still uses SQLite unless `DATABASE_URL` is set
- Render free should use hosted PostgreSQL, not file-based SQLite
- this lets student registration, login, officer creation, skills, companies, contacts, and mentors stay saved properly

The repo also includes a basic [render.yaml](render.yaml) for this setup.

## Deploy on PythonAnywhere

PythonAnywhere is a simpler fallback option when you want to keep SQLite and have the database file persist in your account storage.

### 1. Upload or clone the project

In a PythonAnywhere Bash console:

```bash
git clone https://github.com/Adarsh0437/Skill-Radar.git
cd Skill-Radar
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Create the web app

- Go to the PythonAnywhere dashboard
- Open the `Web` tab
- Click `Add a new web app`
- Choose `Flask`
- Choose `Python 3.12`
- When asked for the app file, use `/home/yourusername/Skill-Radar/app.py`

### 3. Set the source paths

Use these values:

- Source code: `/home/yourusername/Skill-Radar`
- Working directory: `/home/yourusername/Skill-Radar`
- Virtualenv: `/home/yourusername/Skill-Radar/.venv`

### 4. Configure the WSGI file

Open the PythonAnywhere WSGI configuration file from the `Web` tab and replace its contents with:

```python
import os
import sys

PROJECT_DIR = '/home/yourusername/Skill-Radar'
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault('DB_PATH', os.path.join(PROJECT_DIR, 'instance', 'skillradar.db'))

from app import app as application
```

You can also copy the same logic from [pythonanywhere_wsgi.py](pythonanywhere_wsgi.py).

### 5. Create the instance folder

```bash
mkdir -p /home/yourusername/Skill-Radar/instance
```

### 6. Reload the app

Click `Reload` in the `Web` tab.

After the first load:
- the SQLite database file will be created automatically
- default student and officer accounts will be seeded
- student registration, officer creation, login, skills, companies, mentors, and contact settings will all be stored in SQLite

### PythonAnywhere Notes

- you do not need `DATABASE_URL` for PythonAnywhere
- SQLite is the intended free deployment database for this setup
- data persists in your PythonAnywhere account files
- keep `SECRET_KEY` set in your `.env` or WSGI environment if you want a custom secret

## Notes

- `schema.sql` is a legacy MySQL reference file from the earlier version of the project. The current running app uses SQLite by default and optional PostgreSQL via `DATABASE_URL`.
- If `DATABASE_URL` is not set, the app automatically falls back to SQLite.
- Existing seeded students can receive one-time default skill profiles through the schema/bootstrap logic, while future new students do not automatically receive those backfilled defaults.

## Future Improvements

- Resume upload and parsing
- AI-based skill recommendations
- Aptitude and coding test integration
- Interview scheduling
- Email notifications
- Analytics dashboard for placement trends
- Pagination size selector

## Author

Developed by Adarsh  
GitHub: [@Adarsh0437](https://github.com/Adarsh0437)
