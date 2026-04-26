import json
import logging
import re
import urllib.error
import urllib.request

from django.conf import settings

from .ai_recommendation import (
    build_eligibility_explanation,
    exam_to_document,
    job_to_document,
    profile_to_document,
    recommend_exams,
    recommend_jobs,
    recommend_schemes,
    scheme_to_document,
)

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:  # pragma: no cover - deployment fallback
    TfidfVectorizer = None
    cosine_similarity = None


logger = logging.getLogger(__name__)

MAX_CONTEXT_ITEMS = 6
MAX_HISTORY_MESSAGES = 8
MAX_CANDIDATE_ITEMS = 12
KNOWN_COMPANIES = [
    "Accenture",
    "Infosys",
    "TCS",
    "Wipro",
    "Cognizant",
    "Capgemini",
    "IBM",
    "HCL",
    "Tech Mahindra",
]


def normalize_text(text):
    return str(text or "").strip()


def tokenize(text):
    return set(re.findall(r"[a-z0-9]+", normalize_text(text).lower()))


def item_title(item, item_type):
    if item_type == "exam":
        return f"Exam: {item.name}"

    if item_type == "scheme":
        return f"Scheme: {item.name}"

    return f"Job: {item.title}"


def profile_payload(profile):
    skills = normalize_text(getattr(profile, "skills", ""))
    interests = [
        interest.strip()
        for interest in normalize_text(getattr(profile, "interests", "")).split(",")
        if interest.strip()
    ]

    degree = normalize_text(getattr(profile, "college", "")) or normalize_text(
        getattr(profile, "education", "")
    )

    return {
        "education": normalize_text(getattr(profile, "education", "")) or "not provided",
        "degree": degree or "not provided",
        "college": normalize_text(getattr(profile, "college", "")) or "not provided",
        "cgpa": (
            str(getattr(profile, "graduation_cgpa", "") or "").strip() or "not provided"
        ),
        "skills": skills or "not provided",
        "location": normalize_text(getattr(profile, "location", "")) or "not provided",
        "interests": interests or ["not provided"],
        "experience": "not provided",
        "income": normalize_text(getattr(profile, "income", "")) or "not provided",
        "class_10_percentage": (
            str(getattr(profile, "class_10_percentage", "") or "").strip() or "not provided"
        ),
        "class_12_percentage": (
            str(getattr(profile, "class_12_percentage", "") or "").strip() or "not provided"
        ),
        "semester_marks": normalize_text(getattr(profile, "semester_marks", "")) or "not provided",
    }


def missing_profile_fields(profile):
    payload = profile_payload(profile)
    missing = []

    if payload["education"] == "not provided":
        missing.append("education")
    if payload["cgpa"] == "not provided":
        missing.append("CGPA")
    if payload["skills"] == "not provided":
        missing.append("skills")
    if payload["location"] == "not provided":
        missing.append("location")
    if payload["interests"] == ["not provided"]:
        missing.append("interests")

    return missing


def query_focus(query):
    text = normalize_text(query).lower()

    if any(
        term in text
        for term in [
            "offer",
            "offers",
            "which should i join",
            "which company should i join",
            "joining",
            "ctc",
            "package",
        ]
    ):
        return "offer"

    if any(
        term in text
        for term in [
            "job",
            "jobs",
            "off campus",
            "off-campus",
            "internship",
            "internships",
            "apprenticeship",
            "hiring",
            "career",
            "vacancy",
            "resume",
        ]
    ):
        return "job"

    if any(
        term in text
        for term in [
            "scheme",
            "scholarship",
            "benefit",
            "financial aid",
            "grant",
            "subsidy",
            "government support",
        ]
    ):
        return "scheme"

    if any(
        term in text
        for term in [
            "exam",
            "prepare",
            "preparation",
            "study",
            "syllabus",
            "roadmap",
            "jee",
            "neet",
            "upsc",
            "gate",
        ]
    ):
        return "exam"

    return "general"


def query_mentions_generic_portal(query):
    text = normalize_text(query).lower()
    return any(
        term in text
        for term in [
            "portal",
            "portals",
            "website",
            "websites",
            "government portal",
            "job site",
            "job sites",
            "where should i search",
            "where can i apply",
        ]
    )


def serialize_item(item, item_type, profile):
    explanation = build_eligibility_explanation(profile, item, item_type)

    if item_type == "exam":
        body = {
            "type": "exam",
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "opportunity_type": item.exam_type,
            "location": item.location,
            "mode": item.mode,
            "date": str(item.date or "Not listed"),
            "registration_window": getattr(item, "registration_window", "Not listed"),
            "eligibility": item.e_eligibility,
            "conducting_body": getattr(item, "conducting_body", ""),
            "application_fee": getattr(item, "application_fee", ""),
            "salary_package": getattr(item, "salary_package", ""),
            "required_skills": getattr(item, "required_skills", ""),
            "details": item.additional_info or "",
            "source_url": getattr(item, "source_url", ""),
        }
    elif item_type == "scheme":
        body = {
            "type": "scheme",
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "opportunity_type": item.scheme_type,
            "location": item.location,
            "date": str(item.date or "Not listed"),
            "registration_window": getattr(item, "registration_window", "Not listed"),
            "eligibility": item.s_eligibility,
            "description": item.description or "",
            "benefits": getattr(item, "benefit_summary", item.benefits or ""),
            "required_documents": getattr(item, "required_documents", ""),
            "details": item.additional_info or "",
            "source_url": getattr(item, "source_url", ""),
        }
    else:
        body = {
            "type": "job",
            "id": item.id,
            "name": item.title,
            "company_or_org": item.company_or_org,
            "category": item.sector,
            "opportunity_type": item.get_opportunity_type_display(),
            "location": item.location,
            "date": str(item.effective_deadline or "Not listed"),
            "registration_window": item.registration_window,
            "eligibility": item.qualification,
            "required_skills": item.required_skills,
            "compensation": item.compensation_summary,
            "compensation_type": item.get_compensation_type_display(),
            "description": item.description or "",
            "source_url": item.source_url,
            "application_url": item.application_url,
            "verification_notes": item.verification_notes,
        }

    body["ai_explanation"] = explanation
    return body


def extract_company_names(query):
    text = normalize_text(query).lower()
    companies = []

    for company in KNOWN_COMPANIES:
        if company.lower() in text:
            companies.append(company)

    return companies


def searchable_document(item, item_type):
    if item_type == "exam":
        return exam_to_document(item)

    if item_type == "job":
        return job_to_document(item)

    return scheme_to_document(item)


def candidate_rows(profile, focus, exams, schemes, jobs, query):
    query_is_portal_hunting = query_mentions_generic_portal(query)

    if focus == "offer":
        return []

    if focus == "job":
        ranked_jobs = recommend_jobs(profile, jobs)[:MAX_CANDIDATE_ITEMS]
        if not query_is_portal_hunting:
            ranked_jobs = sorted(
                ranked_jobs,
                key=lambda item: (
                    getattr(item, "opportunity_type", "") == "career_portal",
                    -getattr(item, "ai_score", 0),
                ),
            )

        return [
            (
                "job",
                item,
                searchable_document(item, "job"),
                getattr(item, "ai_score", 0) / 100.0,
            )
            for item in ranked_jobs
        ]

    if focus == "scheme":
        ranked_schemes = recommend_schemes(profile, schemes)[:MAX_CANDIDATE_ITEMS]
        return [
            (
                "scheme",
                item,
                searchable_document(item, "scheme"),
                getattr(item, "ai_score", 0) / 100.0,
            )
            for item in ranked_schemes
        ]

    if focus == "exam":
        ranked_exams = recommend_exams(profile, exams)[:MAX_CANDIDATE_ITEMS]
        return [
            (
                "exam",
                item,
                searchable_document(item, "exam"),
                getattr(item, "ai_score", 0) / 100.0,
            )
            for item in ranked_exams
        ]

    rows = []

    for item in recommend_jobs(profile, jobs)[:4]:
        rows.append(
            (
                "job",
                item,
                searchable_document(item, "job"),
                getattr(item, "ai_score", 0) / 100.0,
            )
        )

    for item in recommend_schemes(profile, schemes)[:4]:
        rows.append(
            (
                "scheme",
                item,
                searchable_document(item, "scheme"),
                getattr(item, "ai_score", 0) / 100.0,
            )
        )

    for item in recommend_exams(profile, exams)[:4]:
        rows.append(
            (
                "exam",
                item,
                searchable_document(item, "exam"),
                getattr(item, "ai_score", 0) / 100.0,
            )
        )

    return rows[:MAX_CANDIDATE_ITEMS]


def fallback_profile_rows(profile, focus, exams, schemes, jobs, limit):
    if focus == "offer":
        return []

    if focus == "job":
        return [("job", item) for item in recommend_jobs(profile, jobs)[:limit]]

    if focus == "scheme":
        return [("scheme", item) for item in recommend_schemes(profile, schemes)[:limit]]

    if focus == "exam":
        return [("exam", item) for item in recommend_exams(profile, exams)[:limit]]

    rows = []

    for item in recommend_jobs(profile, jobs)[:2]:
        rows.append(("job", item))

    for item in recommend_schemes(profile, schemes)[:2]:
        rows.append(("scheme", item))

    for item in recommend_exams(profile, exams)[:2]:
        rows.append(("exam", item))

    return rows[:limit]


def retrieve_relevant_items(profile, query, exams, schemes, jobs=None, limit=MAX_CONTEXT_ITEMS):
    jobs = list(jobs or [])
    exams = list(exams)
    schemes = list(schemes)
    focus = query_focus(query)
    rows = candidate_rows(profile, focus, exams, schemes, jobs, query)

    if not rows:
        return []

    profile_context = profile_to_document(profile)
    query_document = f"{query}\n{profile_context}"

    if TfidfVectorizer is not None and cosine_similarity is not None:
        documents = [query_document, *[row[2] for row in rows]]
        matrix = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        ).fit_transform(documents)
        similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
        scored_rows = []

        for similarity, (item_type, item, _, profile_score) in zip(similarities, rows):
            score = (float(similarity) * 0.62) + (profile_score * 0.38)

            if (
                focus == "job"
                and getattr(item, "opportunity_type", "") == "career_portal"
                and not query_mentions_generic_portal(query)
            ):
                score -= 0.08

            scored_rows.append((score, item_type, item))
    else:
        query_tokens = tokenize(query_document)
        scored_rows = []

        for item_type, item, document, profile_score in rows:
            item_tokens = tokenize(document)
            lexical_score = len(query_tokens & item_tokens) / max(len(query_tokens), 1)
            score = (lexical_score * 0.62) + (profile_score * 0.38)

            if (
                focus == "job"
                and getattr(item, "opportunity_type", "") == "career_portal"
                and not query_mentions_generic_portal(query)
            ):
                score -= 0.08

            scored_rows.append((score, item_type, item))

    scored_rows.sort(key=lambda row: row[0], reverse=True)

    positive_rows = [
        (item_type, item)
        for score, item_type, item in scored_rows
        if score > 0.03
    ][:limit]

    if positive_rows:
        return positive_rows

    return fallback_profile_rows(profile, focus, exams, schemes, jobs, limit)


def conversation_history(history):
    normalized = []

    for item in history or []:
        role = normalize_text(item.get("role", ""))
        content = normalize_text(item.get("content", ""))

        if role not in {"user", "assistant"} or not content:
            continue

        normalized.append({"role": role, "content": content})

    return normalized[-MAX_HISTORY_MESSAGES:]


def build_system_prompt():
    return (
        "You are a career guidance assistant for jobs, exams, skills, internships, "
        "government schemes, and education guidance. Use the user's profile and the "
        "retrieved portal records to give personalized recommendations. Respond "
        "naturally. Do not repeat fixed template messages. If data is missing, ask "
        "for one specific missing field politely. Never suggest irrelevant exams or "
        "jobs. Stay accurate and grounded in the supplied profile and retrieved data."
    )


def build_openai_messages(profile, query, context_items, history=None):
    profile_data = profile_payload(profile)
    missing_fields = missing_profile_fields(profile)
    focus = query_focus(query)

    messages = [
        {
            "role": "system",
            "content": build_system_prompt(),
        },
        {
            "role": "system",
            "content": (
                "User profile: "
                + json.dumps(profile_data, ensure_ascii=True)
            ),
        },
        {
            "role": "system",
            "content": (
                "Query focus: "
                + focus
                + ". Missing profile fields: "
                + (", ".join(missing_fields) if missing_fields else "none")
            ),
        },
        {
            "role": "system",
            "content": (
                "Retrieved portal records: "
                + json.dumps(context_items, ensure_ascii=True)
            ),
        },
    ]

    messages.extend(conversation_history(history))
    messages.append({"role": "user", "content": normalize_text(query)})
    return messages


def call_openai_llm(messages):
    api_key = getattr(settings, "OPENAI_API_KEY", "")

    if not api_key:
        return None, "OPENAI_API_KEY is not configured."

    base_url = getattr(
        settings,
        "OPENAI_API_BASE",
        "https://api.openai.com/v1",
    ).rstrip("/")
    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    timeout = int(getattr(settings, "OPENAI_TIMEOUT", 20))
    temperature = float(getattr(settings, "OPENAI_TEMPERATURE", 0.7))
    top_p = float(getattr(settings, "OPENAI_TOP_P", 0.9))

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": 900,
    }

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, f"LLM request failed: {exc}"

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None, "LLM response did not contain an answer."

    return normalize_text(content), None


def local_grounded_answer(query, context_items, profile=None):
    profile = profile or object()
    profile_data = profile_payload(profile)
    missing = missing_profile_fields(profile)
    focus = query_focus(query)
    companies = extract_company_names(query)

    if focus == "offer":
        company_line = ", ".join(companies) if companies else "the companies you mentioned"
        primary_track = "software engineering"

        skills_text = profile_data["skills"].lower()
        if any(term in skills_text for term in ["django", "python", "java", "dbms", "sql"]):
            primary_track = "backend or full-stack software roles"
        elif any(term in skills_text for term in ["excel", "power bi", "analytics", "data"]):
            primary_track = "data or analytics roles"

        lines = [
            f"For a fresher profile like yours, I would compare {company_line} mainly on role quality, learning curve, bond, location, and fixed pay, not just brand name.",
            "",
            f"Your current profile suggests you should prioritize {primary_track} because your saved skills are {profile_data['skills']} and your CGPA is {profile_data['cgpa']}.",
        ]

        if {"TCS", "Infosys", "Wipro", "Accenture"}.issubset(set(companies)):
            lines.extend(
                [
                    "",
                    "If the role, pay, and location are broadly similar, my default shortlist would be:",
                    "1. Accenture or Infosys for stronger early-career project exposure and broader developer learning.",
                    "2. TCS for stability, scale, and internal mobility.",
                    "3. Wipro if the exact project, manager, or tech stack is clearly better than the others.",
                ]
            )

        lines.extend(
            [
                "",
                "My practical rule for you:",
                "- Pick the offer that gives real coding, backend, data, or project ownership closest to your skills.",
                "- Avoid choosing only by highest headline CTC if the role is support-heavy, has a bond, or weak learning.",
                "- Prefer the offer with better tech stack, training, mentor quality, and project allocation clarity.",
            ]
        )

        lines.extend(
            [
                "",
                "To rank these offers properly, send these missing details:",
                "- role name",
                "- fixed CTC and variable pay",
                "- location",
                "- bond or service agreement",
                "- tech stack or project type",
            ]
        )

        return "\n".join(lines)

    if focus == "job":
        lines = [
            f"Based on your profile, I would prioritize job tracks aligned with {profile_data['skills']} rather than generic portals.",
            "",
        ]
    elif focus == "scheme":
        lines = [
            "Based on your current profile, these scheme directions look the most relevant right now.",
            "",
        ]
    elif focus == "exam":
        lines = [
            "Based on your current profile, these exam directions look the most relevant right now.",
            "",
        ]
    else:
        lines = [
            "Here is a profile-aware answer using the current portal data and your saved academic details.",
            "",
        ]

    if context_items:
        lines.append("Most relevant matches right now:")
        lines.append("")

        for index, item in enumerate(context_items[:4], start=1):
            explanation = item["ai_explanation"]
            summary_bits = [
                f"{index}. {item['name']} ({item['type']})",
                f"   Why it fits: {explanation['matching_factors'][0]}",
                f"   Confidence: {explanation['confidence']}% - {explanation['verdict']}",
            ]

            if item["type"] == "job":
                summary_bits.append(
                    f"   Compensation: {item.get('compensation', 'Not listed')}"
                )
                summary_bits.append(
                    f"   Registration: {item.get('registration_window', 'Not listed')}"
                )
            elif item["type"] in {"exam", "scheme"}:
                summary_bits.append(
                    f"   Eligibility: {item.get('eligibility', 'Not listed')}"
                )
                summary_bits.append(
                    f"   Date: {item.get('date', 'Not listed')}"
                )

            lines.extend(summary_bits)
    else:
        lines.extend(
            [
                "I do not see a strong direct portal record for that question right now.",
                "I would narrow the answer further using your education, skills, location, and the exact role or exam name you want to target.",
            ]
        )

    lines.extend(
        [
            "",
            "Profile signals I used:",
            f"- Education / degree: {profile_data['education']} / {profile_data['degree']}",
            f"- CGPA: {profile_data['cgpa']}",
            f"- Skills: {profile_data['skills']}",
            f"- Location: {profile_data['location']}",
            f"- Interests: {', '.join(profile_data['interests'])}",
        ]
    )

    if focus == "job":
        lines.extend(
            [
                "",
                "Suggested next steps:",
                "- Keep backend-friendly resume projects visible.",
                "- Strengthen aptitude, SQL, DBMS, OOP, and interview communication for off-campus hiring.",
                "- Apply first to roles closest to Python, Django, SQL, Java, and DBMS rather than broad portals.",
            ]
        )
    elif focus == "scheme":
        lines.extend(
            [
                "",
                "Suggested next steps:",
                "- Check eligibility carefully against education, income, and category rules.",
                "- Keep Aadhaar, marksheets, bank details, and any income/category documents ready.",
            ]
        )
    elif focus == "exam":
        lines.extend(
            [
                "",
                "Suggested next steps:",
                "- Shortlist one or two target exams instead of spreading preparation too wide.",
                "- Build a weekly plan around syllabus, mocks, and previous-year questions.",
            ]
        )

    if missing:
        lines.extend(
            [
                "",
                "To improve the next answer, add this profile field:",
                f"- {missing[0]}",
            ]
        )

    lines.extend(
        [
            "",
            "Verify final eligibility, deadlines, and official application rules from the linked source before applying.",
        ]
    )

    return "\n".join(lines)


def answer_question(profile, query, exams, schemes, jobs=None, history=None):
    if hasattr(profile, "refresh_from_db"):
        profile.refresh_from_db()

    query = normalize_text(query)

    if not query:
        return {
            "answer": "Ask me about jobs, internships, exams, schemes, skills, or what to improve in your profile for better matches.",
            "provider": "local-semantic-rag",
            "items": [],
        }

    relevant = retrieve_relevant_items(profile, query, exams, schemes, jobs)
    context_items = [
        serialize_item(item, item_type, profile)
        for item_type, item in relevant
    ]

    messages = build_openai_messages(profile, query, context_items, history)

    logger.info(
        "AI assistant request | message=%s | profile=%s | results=%s",
        query,
        json.dumps(profile_payload(profile), ensure_ascii=True),
        json.dumps(
            [
                {
                    "type": item["type"],
                    "name": item["name"],
                    "location": item.get("location", ""),
                    "category": item.get("category", ""),
                }
                for item in context_items
            ],
            ensure_ascii=True,
        ),
    )

    llm_answer, llm_error = call_openai_llm(messages)

    if llm_answer:
        answer = llm_answer
        provider = "openai-rag"
    else:
        answer = local_grounded_answer(query, context_items, profile)
        provider = "local-semantic-rag"

    logger.info(
        "AI assistant response | provider=%s | error=%s | answer=%s",
        provider,
        llm_error or "",
        answer,
    )

    source_cards = [
        {
            "title": item_title(item, item_type),
            "type": item_type,
            "id": item.id,
            "category": getattr(item, "category", getattr(item, "sector", "")),
            "location": item.location,
            "date": str(
                getattr(item, "date", "")
                or getattr(item, "effective_deadline", "")
                or getattr(item, "deadline", "")
                or "Not listed"
            ),
            "compensation": item.compensation_summary if item_type == "job" else "",
            "registration_window": item.registration_window if item_type == "job" else "",
            "confidence": build_eligibility_explanation(profile, item, item_type)["confidence"],
        }
        for item_type, item in relevant
    ]

    return {
        "answer": answer,
        "provider": provider,
        "provider_note": llm_error or "",
        "items": source_cards,
    }
