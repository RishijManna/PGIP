# Government PGIP Portal

Personalized Government Information Portal (PGIP) is a Django web application that helps users discover relevant government schemes, competitive exams, jobs, internships, and apprenticeships from one place. It combines profile-based filtering, deadline tracking, and an AI-powered assistant to make public information easier to act on.

Live app: [https://rishijmanna.pythonanywhere.com/](https://rishijmanna.pythonanywhere.com/)

## Features

- OTP-based login using email
- User profile with education, income, location, caste, interests, skills, marks, and academic details
- Personalized recommendations for exams, schemes, and job opportunities
- AI eligibility explanations with matching factors, concerns, and suggested documents
- AI assistant for questions about schemes, exams, jobs, internships, apprenticeships, and offer decisions
- Search across exams, schemes, and opportunities
- Calendar reminders for exams, schemes, jobs, and personal tasks
- Document upload support for user records
- Source-backed records for opportunities, schemes, and exams
- Optional OpenAI integration with local semantic fallback when no API key is configured

## Tech Stack

- Python
- Django 5
- SQLite by default
- PostgreSQL supported through `DATABASE_URL`
- WhiteNoise for static files
- Gunicorn for deployment
- scikit-learn for local recommendation and semantic matching

## Project Structure

```text
PGIP_SQL/
|-- manage.py
|-- requirements.txt
|-- Procfile
|-- my_project/              # Django project settings and URLs
|-- my_app/                  # Main application logic, models, views, services
|-- core/
|   |-- templates/           # HTML templates
|   |-- static/              # Project static assets
|-- documents/               # Sample uploaded documents
|-- media/                   # User-uploaded media
|-- staticfiles/             # Collected static files
|-- db.sqlite3               # Local development database
```

## Main Modules

- `my_app/models.py`: exams, schemes, opportunities, OTPs, reminders, documents, and user profile models
- `my_app/views.py`: dashboard, login flow, recommendations, AI assistant, profile, search, and calendar views
- `my_app/services/ai_recommendation.py`: profile-aware ranking and eligibility reasoning
- `my_app/services/ai_assistant.py`: grounded assistant with OpenAI-backed or local semantic responses
- `my_app/management/commands/seed_data.py`: seeds sample exam and scheme data
- `my_app/management/commands/sync_real_opportunities.py`: imports source-backed records and optional JSON feeds

## Setup

1. Create and activate a virtual environment.
2. Install dependencies.
3. Add environment variables in a `.env` file.
4. Run migrations.
5. Load initial data.
6. Start the server.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py sync_real_opportunities
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

## Environment Variables

Create a `.env` file in the project root.

```env
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
DATABASE_URL=sqlite:///db.sqlite3
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_TIMEOUT=20
REAL_EXAM_FEEDS=
REAL_SCHEME_FEEDS=
REAL_OPPORTUNITY_FEEDS=
```

Notes:

- `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` are required for OTP login by email.
- If `OPENAI_API_KEY` is not set, the AI assistant still works using local semantic matching.
- `DATABASE_URL` is optional for local SQLite, but useful for PostgreSQL deployment.
- Feed variables accept comma-separated JSON URLs for extra records.

## Data Commands

Seed sample exam and scheme records:

```bash
python manage.py seed_data
```

Sync bundled source-backed records plus optional JSON feeds:

```bash
python manage.py sync_real_opportunities
```

Replace existing data before syncing:

```bash
python manage.py sync_real_opportunities --replace-seed-data
```

## Supported JSON Feed Variables

- `REAL_EXAM_FEEDS`
- `REAL_SCHEME_FEEDS`
- `REAL_OPPORTUNITY_FEEDS`

Example:

```env
REAL_EXAM_FEEDS=https://example.com/exams.json
REAL_SCHEME_FEEDS=https://example.com/schemes.json
REAL_OPPORTUNITY_FEEDS=https://example.com/jobs.json,https://example.com/offcampus.json
```

## Key Routes

- `/` - dashboard
- `/login/` - email login
- `/verify_otp/` - OTP verification
- `/profile/` - profile and document management
- `/recommendations/` - AI recommendations
- `/ai-assistant/` - AI assistant UI
- `/calendar/` - reminders calendar
- `/search/` - search results
- `/details/<item_type>/<item_id>/` - detail page for exams, schemes, and jobs

## Deployment

This project includes a `Procfile` for Gunicorn:

```bash
gunicorn my_project.wsgi:application --timeout 120 --workers 4
```

Static files are served with WhiteNoise, and production databases can be configured through `DATABASE_URL`.

## Future Improvements

- Add automated tests for views, services, and recommendation logic
- Add admin dashboards for managing live records
- Improve AI citation and source-trace display in the assistant
- Add richer filtering for job and scheme discovery

## License

This project currently does not define a license.
