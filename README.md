# SkillRadar

Smart Campus Placement & Skill Analyzer built with Flask, SQLite/PostgreSQL, Jinja2, vanilla JavaScript, and Plotly.

`SkillRadar` helps students understand placement readiness through skill self-assessment and benchmark comparison, while giving placement officers a centralized platform to manage students, company drives, contact information, and alumni mentors.

Repository: [Adarsh0437/Skill-Radar](https://github.com/Adarsh0437/Skill-Radar)

## Overview

Campus placement preparation is often fragmented. Students may know their CGPA, but not how their technical and communication skills compare to placement expectations. Placement officers often manage eligibility, company data, and communication through scattered spreadsheets and manual updates.

SkillRadar brings those workflows into a single web application.

Students can:
- register and manage their profile
- rate their core placement skills on a `0-10` scale
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
- manage placement office contact information
- manage alumni mentor profiles

## Key Features

### Student Features
- Secure student registration and login
- Skill self-rating form (`0-10`) for:
  - Python
  - SQL
  - Java
  - DSA
  - Communication
  - Problem Solving
  - Web Development
  - Machine Learning
- Radar chart comparison between student skills and industry standards
- Skill gap percentage calculation with suggested focus areas
- Placement hub with eligibility badges based on CGPA + required skill threshold
- Profile update and account management

### Placement Officer Features
- Role-based officer login
- Student dashboard with:
  - department filter
  - minimum CGPA filter
  - student search
  - CSV export
- Student record update and delete actions
- Company add, update, delete, and search
- Editable placement office contact details
- Editable alumni mentor cards

### UI / Experience Features
- Dark academic theme with navy and gold palette
- Plotly radar chart visualization
- Premium card-based interface
- Mobile-responsive layouts
- Custom themed dropdowns
- Modal-based mentor editing
- Inline form validation feedback

## Tech Stack

- Backend: Flask
- Authentication: Flask-Login
- Database: SQLite locally and on PythonAnywhere free, PostgreSQL for Render free
- Frontend: HTML, CSS, Jinja2 templates, vanilla JavaScript
- Charts: Plotly.js

## Project Structure

```text
Skill-Radar/
├── app.py
├── config.py
├── models.py
├── pythonanywhere_wsgi.py
├── requirements.txt
├── schema.sql
├── static/
│   ├── css/style.css
│   ├── img/skillradar-logo.svg
│   └── js/chart.js
└── templates/
    ├── base.html
    ├── contact.html
    ├── dashboard.html
    ├── login.html
    ├── officer_panel.html
    ├── placement_hub.html
    ├── register.html
    ├── skill_form.html
    └── visualize.html
```

## How It Works

1. Students register with academic details such as name, email, CGPA, roll number, and department.
2. Students log in and submit self-ratings for core placement skills.
3. The app compares student ratings with predefined industry benchmark scores.
4. A radar chart visually shows the difference between current skills and expected industry levels.
5. The placement hub checks company eligibility using student CGPA and required tracked skill thresholds from the company profile.
6. Officers can search, filter, export, and manage student and company records from the admin side.
7. Contact and mentor information can be updated directly by the officer through the UI.

## Skill Gap Logic

SkillRadar uses a simple and practical gap formula:

- Gap per skill = `max(0, industry_score - student_score)`
- Overall skill gap % = `(sum of gaps / sum of industry benchmark scores) * 100`

This helps students quickly understand where improvement is needed most.

## Placement Eligibility Logic

Placement Hub eligibility is based on:

- `student.cgpa >= company.min_cgpa`
- if the company's `skills_required` text mentions tracked skills like `Python`, `SQL`, `DSA`, or `Web Dev`, those skills must each be at least `6/10`

This gives a more practical result than CGPA-only filtering while still keeping company setup simple for officers.

## Real-World Use Case

SkillRadar is useful for real college placement cells because it:
- helps students identify weak skill areas early
- reduces dependency on manual spreadsheets
- centralizes company and student placement data
- improves transparency in eligibility tracking
- gives officers better visibility into campus readiness

Example:
- A student may discover a strong CGPA but weak DSA and SQL ratings.
- A placement officer may filter students from a specific department above a CGPA cutoff for a drive.
- The placement cell can instantly update office contact info or mentor details without touching code.

## Screenshots

You can add screenshots here after uploading them to the repository.

Suggested sections:
- Login page
- Student dashboard
- Skill form
- Radar chart
- Placement hub
- Officer panel
- Contact and mentor page

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

### 4. Run the app

The app uses SQLite locally by default and creates the database automatically on first run.

```bash
flask --app app run
```

Open: http://127.0.0.1:5000

### Default Accounts

- **Officer**: `officer@campus.edu` / `admin123`
- **Student 1**: `student1@campus.edu` / `pass123`
- **Student 2**: `student2@campus.edu` / `pass123`

```text
http://127.0.0.1:5000
```

## Test Credentials

### Officer
- Email: `officer@campus.edu`
- Password: `admin123`

### Students
- Email: `student1@campus.edu`
- Password: `pass123`

- Email: `student2@campus.edu`
- Password: `pass123`

## Deploy On Render Free

Render is the primary cloud deployment path for this project. For reliable persistence on the free plan, use a free hosted PostgreSQL database such as Neon or Supabase.

### 1. Push the project to GitHub

Make sure your latest code is in the GitHub repo you want Render to deploy from.

### 2. Create a new Render Web Service

- Choose `New +` -> `Web Service`
- Connect your GitHub repository
- Select the `Skill-Radar` repo

### 3. Create a free hosted PostgreSQL database

Use either:
- Neon Postgres
- Supabase Postgres

Copy the connection string they provide. It will look like:

```text
postgresql://username:password@host/database?sslmode=require
```

### 4. Use these Render settings

- Environment: `Python 3`
- Build Command:

```bash
pip install -r requirements.txt
```

- Start Command:

```bash
gunicorn app:app
```

### 5. Add environment variables

Set these in Render:

- `SECRET_KEY` = your own secret key
- `DATABASE_URL` = your hosted PostgreSQL connection string

### 6. Deploy

After the first deploy:

- the app will automatically create the PostgreSQL schema
- default accounts will be seeded if they do not already exist
- future registrations and officer-created records will persist in the hosted database

### Render Notes

- local development still uses SQLite unless `DATABASE_URL` is set
- Render free should use hosted PostgreSQL, not file-based SQLite
- this lets student registration, login, officer creation, skills, companies, contacts, and mentors stay saved properly on the free plan

## Deploy On PythonAnywhere Free

PythonAnywhere is a simpler fallback deployment option when you want to keep SQLite and have the database file persist in your account storage.

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
- Choose `Manual configuration`
- Choose `Python 3.12`

### 3. Set the source paths

Use these values:

- Source code: `/home/yourusername/Skill-Radar`
- Working directory: `/home/yourusername/Skill-Radar`

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

You can also copy the same logic from [pythonanywhere_wsgi.py](/d:/ICTProject/smart_campus/pythonanywhere_wsgi.py).

### 5. Set up the virtualenv

In the `Web` tab, set the virtualenv path to:

```text
/home/yourusername/Skill-Radar/.venv
```

### 6. Reload the app

Click `Reload` in the `Web` tab.

After the first load:
- the SQLite database file will be created automatically
- default student and officer accounts will be seeded
- student registration, officer creation, login, skills, companies, mentors, and contact settings will all be stored in SQLite

### PythonAnywhere Notes

- you do not need `DATABASE_URL` for PythonAnywhere free
- SQLite is the intended free deployment database for this setup
- data will persist in your PythonAnywhere account files
- keep `SECRET_KEY` set in your `.env` or WSGI environment if you want a custom secret

## Notes

- `schema.sql` is a legacy MySQL reference file from the original version of the project. The current running app uses SQLite locally/PythonAnywhere and optional PostgreSQL via `DATABASE_URL`.
- If `DATABASE_URL` is not set, the app automatically falls back to SQLite.

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
