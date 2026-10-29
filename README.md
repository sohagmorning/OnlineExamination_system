# Online Examination System

A Flask-based online examination system with student registration, subject-based exams, results, and an admin panel.

## Requirements

- Python 3
- Packages listed in `requirements.txt`

## Run locally

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in a browser.

The application creates `exam.db` locally when it starts. The database file is intentionally excluded from Git so local users and results are not published.

## Vercel deployment

The project includes `api/index.py` and `vercel.json` for Vercel's Python runtime. Import the GitHub repository into Vercel and deploy the `main` branch.

Vercel's serverless filesystem is temporary, so the SQLite database used there is stored under `/tmp` and can be reset between deployments or function instances. For persistent users, questions, and results, use a hosted database such as PostgreSQL.

## Project structure

- `app.py` - Flask application and SQLite database logic
- `templates/` - Jinja2 HTML templates
- `static/css/` - application styles
- `static/js/` - browser-side JavaScript
