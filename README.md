# SkillRadar

Smart Campus Placement & Skill Analyzer built with Flask, MySQL, Jinja2, vanilla JavaScript, and Plotly.

`SkillRadar` helps students understand placement readiness through skill self-assessment and benchmark comparison, while giving placement officers a centralized platform to manage students, company drives, contact information, and alumni mentors.

Repository: [Adarsh0437/Skill-Radar](https://github.com/Adarsh0437/Skill-Radar)

## Overview

Campus placement preparation is often fragmented. Students may know their CGPA, but not how their technical and communication skills compare to placement expectations. Placement officers often manage eligibility, company data, and communication through scattered spreadsheets and manual updates.

SkillRadar brings those workflows into a single web application.

Students can:
- register and manage their profile
- rate their core placement skills
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
- Skill self-rating form for:
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
- Placement hub with eligibility badges
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
- Database: MySQL + PyMySQL
- Frontend: HTML, CSS, Jinja2 templates, vanilla JavaScript
- Charts: Plotly.js

## Project Structure

```text
smart_campus/
├── app.py
├── config.py
├── models.py
├── requirements.txt
├── schema.sql
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── chart.js
└── templates/
    ├── base.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── skill_form.html
    ├── visualize.html
    ├── placement_hub.html
    ├── contact.html
    └── officer_panel.html
```

## How It Works

1. Students register with academic details such as name, email, CGPA, roll number, and department.
2. Students log in and submit self-ratings for core placement skills.
3. The app compares student ratings with predefined industry benchmark scores.
4. A radar chart visually shows the difference between current skills and expected industry levels.
5. The placement hub checks company eligibility using student CGPA and company minimum CGPA.
6. Officers can search, filter, export, and manage student and company records from the admin side.
7. Contact and mentor information can be updated directly by the officer through the UI.

## Skill Gap Logic

SkillRadar uses a simple and practical gap formula:

- Gap per skill = `max(0, industry_score - student_score)`
- Overall skill gap % = `(sum of gaps / sum of industry benchmark scores) * 100`

This helps students quickly understand where improvement is needed most.

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

### 4. Create the MySQL database

```sql
CREATE DATABASE smart_campus;
```

Then run `schema.sql` on that database.

### 5. Configure database credentials

Edit `config.py` or set environment variables:

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `SECRET_KEY`

### 6. Run the app

```bash
flask --app app run
```

Open:

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
