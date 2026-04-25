Government_PGIP_Portal

Personalized Government Information Portal (PGIP)

In today's digital landscape, individuals often face challenges in keeping track of government schemes, competitive exams, job openings, internships, apprenticeships, and tax-related updates because information is scattered across many sources. PGIP solves this by providing a centralized, smart web application that delivers tailored public-service and career information based on each user's profile.

Users can create accounts and provide details such as age, gender, education, employment type, income status, domicile state, skills, 10th/12th marks, graduation CGPA, semester marks, and academic documents. The system uses this data to filter and recommend schemes, exam notifications, jobs, internships, apprenticeships, and other opportunities aligned with eligibility and interests.

The platform includes:

- Personalized alerts and deadline reminders
- Eligibility-based scheme, exam, and job recommendations
- Document checklists for applications
- Source-backed real-world opportunity records
- Compensation, stipend, CTC, registration start date, and last-date fields for jobs and internships
- Streamlined updates on government services

LINK -> [https://rishijmanna.pythonanywhere.com/]

## GenAI Upgrade

PGIP now includes a RAG-style AI assistant for schemes, exams, jobs, internships, apprenticeships, and offer decisions:

- Natural-language chatbot over portal exams, schemes, jobs, and career records
- Profile-aware retrieval using education, income, location, interests, gender, caste, skills, and marks
- Skill and marks-aware matching using skills, 10th marks, 12th marks, CGPA, and semester marks
- AI eligibility explanations with confidence, matching factors, concerns, and suggested documents
- Exam preparation roadmaps when a student asks what to study for a particular exam
- Scheme guidance for scholarships, financial aid, training, and welfare support
- Job/off-campus guidance with compensation and registration deadline context
- Company offer comparison guidance for students choosing between multiple job offers
- Optional OpenAI-backed generation when `OPENAI_API_KEY` is configured
- Local semantic RAG fallback when no API key is available, so the demo still works offline

Real-world opportunity sync:

```bash
python manage.py sync_real_opportunities
```

The sync command adds source-backed records for current and official sources such as UPSC exam calendars, myScheme, National Scholarship Portal, PM Internship Scheme, DRDO INMAS, J&K Bank, HPCL Careers, NCS, Apprenticeship India, and major IT career portals. For official portals that do not publish a fixed CTC, fee or last date, the app shows "verify from official notification" or "varies by listing" instead of inventing numbers.

To run the portal only from source-backed sync data instead of `seed_data.py`, use:

```bash
python manage.py sync_real_opportunities --replace-seed-data
```

That command clears existing exams, schemes and job opportunities, then repopulates them from the sync command and any configured feeds.

JSON feed records can include:

Exam feeds via `REAL_EXAM_FEEDS`:

- `name`, `exam_type`, `category`, `conducting_body`, `location`, `mode`
- `date`, `registration_start_date`, `registration_end_date`
- `application_fee`, `salary_package`, `required_skills`
- `eligibility`, `source_name`, `source_url`, `official_notification_url`, `application_url`

Scheme feeds via `REAL_SCHEME_FEEDS`:

- `name`, `category`, `scheme_type`, `description`, `eligibility`
- `benefits`, `benefit_amount`, `required_documents`
- `registration_start_date`, `registration_end_date`
- `source_name`, `source_url`, `official_notification_url`, `application_url`

Opportunity feeds via `REAL_OPPORTUNITY_FEEDS`:

- `title`, `company`, `opportunity_type`, `sector`, `location`
- `qualification`, `skills`, `min_10th_percentage`, `min_12th_percentage`, `min_cgpa`
- `compensation_type`, `compensation`, `salary`, `stipend`, or `ctc`
- `registration_start_date`, `registration_end_date`, `deadline`
- `source_name`, `source_url`, `official_notification_url`, `application_url`, `data_as_of`

Structured feed import:

```env
REAL_EXAM_FEEDS=https://example.com/exams.json
REAL_SCHEME_FEEDS=https://example.com/schemes.json
REAL_OPPORTUNITY_FEEDS=https://example.com/jobs.json,https://example.com/offcampus.json
```

Optional environment variables:

```env
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_TIMEOUT=20
```

Run locally:

```bash
python manage.py runserver
```
