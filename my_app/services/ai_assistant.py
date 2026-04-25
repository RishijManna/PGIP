import json
import os
import re
import urllib.error
import urllib.request

from .ai_recommendation import (
    build_eligibility_explanation,
    exam_to_document,
    job_to_document,
    profile_to_document,
    scheme_to_document,
)

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:  # pragma: no cover - deployment fallback
    TfidfVectorizer = None
    cosine_similarity = None


MAX_CONTEXT_ITEMS = 6


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


def serialize_item(item, item_type, profile):
    explanation = build_eligibility_explanation(profile, item, item_type)

    if item_type == "exam":
        body = {
            "type": "exam",
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


def searchable_document(item, item_type):
    if item_type == "exam":
        return exam_to_document(item)

    if item_type == "job":
        return job_to_document(item)

    return scheme_to_document(item)


def retrieve_relevant_items(profile, query, exams, schemes, jobs=None, limit=MAX_CONTEXT_ITEMS):
    jobs = jobs or []
    rows = [
        ("exam", item, searchable_document(item, "exam"))
        for item in exams
    ] + [
        ("scheme", item, searchable_document(item, "scheme"))
        for item in schemes
    ] + [
        ("job", item, searchable_document(item, "job"))
        for item in jobs
    ]

    if not rows:
        return []

    profile_context = profile_to_document(profile)
    query_document = f"{query} {profile_context}"

    if TfidfVectorizer is not None and cosine_similarity is not None:
        documents = [query_document, *[row[2] for row in rows]]
        matrix = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        ).fit_transform(documents)
        similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
        scored_rows = [
            (score, row[0], row[1])
            for score, row in zip(similarities, rows)
        ]
    else:
        query_tokens = tokenize(query_document)
        scored_rows = []

        for item_type, item, document in rows:
            item_tokens = tokenize(document)
            score = len(query_tokens & item_tokens) / max(len(query_tokens), 1)
            scored_rows.append((score, item_type, item))

    scored_rows.sort(key=lambda row: row[0], reverse=True)

    top_rows = [
        (item_type, item)
        for score, item_type, item in scored_rows
        if score > 0
    ][:limit]

    if top_rows:
        return top_rows

    return [(item_type, item) for _, item_type, item in scored_rows[:limit]]


def profile_summary(profile):
    return {
        "education": profile.education or "not provided",
        "income": profile.income or "not provided",
        "location": profile.location or "not provided",
        "gender": profile.gender or "not provided",
        "caste": profile.caste or "not provided",
        "interests": profile.interests or "not provided",
        "skills": getattr(profile, "skills", "") or "not provided",
        "10th_percentage": str(getattr(profile, "class_10_percentage", "") or "not provided"),
        "12th_percentage": str(getattr(profile, "class_12_percentage", "") or "not provided"),
        "graduation_cgpa": str(getattr(profile, "graduation_cgpa", "") or "not provided"),
        "semester_marks": getattr(profile, "semester_marks", "") or "not provided",
    }


def build_prompt(profile, query, context_items, history=None):
    history = history or []

    return (
        "You are PGIP AI, a careful assistant for Indian government schemes, "
        "exams, jobs, internships, apprenticeships and off-campus opportunities. "
        "Answer only from the provided portal context. Do not invent "
        "eligibility, benefits, dates, links, or official status. If information "
        "is missing, say what should be verified from the official notification. "
        "Use a helpful, concise tone.\n\n"
        f"User profile:\n{json.dumps(profile_summary(profile), indent=2)}\n\n"
        f"Recent chat history:\n{json.dumps(history[-6:], indent=2)}\n\n"
        f"User question:\n{query}\n\n"
        "Retrieved portal context:\n"
        f"{json.dumps(context_items, indent=2)}\n\n"
        "Answer format:\n"
        "1. Direct answer\n"
        "2. Best matches with reasons, compensation and last date where available\n"
        "3. Documents or next steps\n"
        "4. Anything the user must verify"
    )


def call_openai_llm(prompt):
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        return None, "OPENAI_API_KEY is not configured."

    base_url = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    timeout = int(os.environ.get("OPENAI_TIMEOUT", "20"))

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You answer with grounded, cautious RAG responses for PGIP.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 700,
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
        return data["choices"][0]["message"]["content"].strip(), None
    except (KeyError, IndexError, TypeError):
        return None, "LLM response did not contain an answer."


def looks_like_study_question(query):
    query = query.lower()
    return any(
        term in query
        for term in [
            "study",
            "prepare",
            "preparation",
            "syllabus",
            "roadmap",
            "subjects",
            "topics",
            "particular exam",
        ]
    )


def looks_like_offer_question(query):
    query = query.lower()
    return any(
        term in query
        for term in ["offer", "joining", "company", "companies", "package", "ctc"]
    )


def looks_like_scheme_question(query):
    query = query.lower()
    return any(
        term in query
        for term in ["scheme", "scholarship", "apply", "benefit", "financial aid"]
    )


def looks_like_job_question(query):
    query = query.lower()
    return any(
        term in query
        for term in [
            "job",
            "jobs",
            "off campus",
            "off-campus",
            "internship",
            "apprenticeship",
            "hiring",
            "career",
            "vacancy",
        ]
    )


def exam_study_plan(query, context_items):
    exams = [item for item in context_items if item["type"] == "exam"]

    if not exams:
        return (
            "I could not identify a matching exam in the portal data. Tell me the exact exam name, "
            "and I can create a preparation roadmap."
        )

    exam = exams[0]
    category = normalize_text(exam.get("category", "")).lower()
    plan = [
        f"Study roadmap for {exam['name']}:",
        "",
        f"Eligibility/date in portal: {exam.get('eligibility', 'Not listed')} · {exam.get('date', 'Not listed')}",
        "",
        "1. Start with the official notification and syllabus.",
        "2. Make a topic checklist and mark each topic as weak, medium, or strong.",
        "3. Study concepts first, then solve previous-year questions, then take timed mocks.",
    ]

    if "engineering" in category:
        plan.extend([
            "4. Core subjects: Mathematics, Physics, Chemistry, aptitude/problem solving.",
            "5. For coding or engineering jobs/exams, add DSA, DBMS, OS, CN, OOP, SQL, and one project revision.",
        ])
    elif "medical" in category:
        plan.extend([
            "4. Core subjects: Biology, Chemistry, Physics, NCERT-based revision, diagrams, and daily MCQ practice.",
        ])
    elif "banking" in category:
        plan.extend([
            "4. Core subjects: Quantitative Aptitude, Reasoning, English, General Awareness, Banking Awareness, and speed practice.",
        ])
    elif "civil" in category or "employment" in category:
        plan.extend([
            "4. Core subjects: General Studies, Current Affairs, Quantitative Aptitude, Reasoning, English, and exam-specific paper practice.",
        ])
    else:
        plan.extend([
            "4. Core subjects: revise the category-specific syllabus, aptitude, English, reasoning, and current affairs if applicable.",
        ])

    plan.extend([
        "",
        "Weekly structure:",
        "Weekdays: 2 concept blocks + 1 practice block.",
        "Weekend: 1 mock test + error analysis + backlog clearing.",
        "",
        "Documents to keep ready: "
        + ", ".join(exam["ai_explanation"]["suggested_documents"])
        + ".",
    ])

    return "\n".join(plan)


def offer_comparison_answer(query, profile):
    skills = normalize_text(getattr(profile, "skills", ""))

    return "\n".join([
        "To choose between 3-4 company offers, compare them with a weighted score instead of only CTC:",
        "",
        "1. Role fit: Does the work match your skills and long-term goal?",
        f"   Your saved skills: {skills or 'not added yet'}.",
        "2. Learning curve: product work, mentorship, tech stack, code quality, and training.",
        "3. Compensation: fixed pay, variable pay, joining bonus, relocation, bond, and in-hand salary.",
        "4. Growth: promotion cycle, internal mobility, project quality, and brand value.",
        "5. Stability and risk: company financials, layoffs, bench policy, probation rules.",
        "6. Location and lifestyle: commute, remote policy, work-life balance, night shifts.",
        "",
        "Best practical rule: for a fresher, choose the offer with the strongest role + learning + stability unless another offer has a clearly higher fixed salary without a bond or risky terms.",
        "",
        "Send company names, role, CTC breakup, location, bond, tech stack, and your career goal. I can rank them for you.",
    ])


def scheme_guidance_answer(context_items):
    schemes = [item for item in context_items if item["type"] == "scheme"]

    if not schemes:
        return (
            "I did not find a strong scheme match in the portal data. Update your income, caste/category, location, education, and interests in Profile for better results."
        )

    lines = [
        "Based on your profile, you should first check these kinds of schemes:",
        "",
    ]

    for index, scheme in enumerate(schemes[:5], start=1):
        explanation = scheme["ai_explanation"]
        lines.extend([
            f"{index}. {scheme['name']} ({scheme.get('opportunity_type', 'Scheme')})",
            f"   Why: {explanation['matching_factors'][0]}",
            f"   Confidence: {explanation['confidence']}% · {explanation['verdict']}",
        ])

    lines.extend([
        "",
        "In general, students should check scholarships, fee assistance, skill training, internship/apprenticeship, startup grants, and state-resident schemes.",
        "Keep marksheets, income certificate, Aadhaar, domicile/address proof, bank details, and caste/category certificate ready where applicable.",
    ])

    return "\n".join(lines)


def job_guidance_answer(context_items, profile):
    jobs = [item for item in context_items if item["type"] == "job"]

    if not jobs:
        return (
            "I did not find a strong job or off-campus match in the portal data. "
            "Add skills, 10th/12th marks, graduation CGPA and semester marks in Profile, "
            "then search again with a role like Python developer, banking apprentice or data analyst."
        )

    lines = [
        "Based on your profile, these opportunity types are worth checking first:",
        "",
    ]

    for index, job in enumerate(jobs[:5], start=1):
        explanation = job["ai_explanation"]
        lines.extend([
            f"{index}. {job['name']} - {job.get('company_or_org', 'Organization not listed')}",
            f"   Type: {job.get('opportunity_type', 'Job')}",
            f"   Compensation: {job.get('compensation', 'Not listed')}",
            f"   Registration: {job.get('registration_window', 'Not listed')}",
            f"   Why: {explanation['matching_factors'][0]}",
            f"   Confidence: {explanation['confidence']}% - {explanation['verdict']}",
        ])

    profile_skills = normalize_text(getattr(profile, "skills", ""))
    lines.extend([
        "",
        f"Your saved skills: {profile_skills or 'not added yet'}.",
        "For IT/off-campus roles, strengthen DSA, SQL, one backend or frontend stack, aptitude, resume projects and interview communication.",
        "For government apprenticeships/jobs, check official notification, eligibility cutoff, age, category relaxation, exam pattern, stipend/pay scale and last date before applying.",
    ])

    return "\n".join(lines)


def local_grounded_answer(query, context_items, profile=None):
    if looks_like_offer_question(query):
        return offer_comparison_answer(query, profile)

    if looks_like_study_question(query):
        return exam_study_plan(query, context_items)

    if looks_like_job_question(query):
        return job_guidance_answer(context_items, profile)

    if looks_like_scheme_question(query):
        return scheme_guidance_answer(context_items)

    if not context_items:
        return (
            "I could not find matching exams or schemes in the portal database. "
            "Try asking with your education, location, income range, or category."
        )

    lines = [
        "Based on your profile and the portal database, these are the strongest matches I found:",
        "",
    ]

    for index, item in enumerate(context_items[:4], start=1):
        explanation = item["ai_explanation"]
        lines.extend(
            [
                f"{index}. {item['name']} ({item['type'].title()})",
                f"   Match: {explanation['verdict']} with {explanation['confidence']}% confidence.",
                f"   Why: {' '.join(explanation['matching_factors'][:2])}",
            ]
        )

        if item["type"] == "job":
            lines.append(f"   Compensation: {item.get('compensation', 'Not listed')}")
            lines.append(f"   Registration: {item.get('registration_window', 'Not listed')}")

        if explanation["concerns"]:
            lines.append(f"   Check: {explanation['concerns'][0]}")

    documents = []
    for item in context_items[:3]:
        documents.extend(item["ai_explanation"]["suggested_documents"])

    unique_documents = list(dict.fromkeys(documents))[:6]

    lines.extend(
        [
            "",
            "Suggested documents to keep ready:",
            ", ".join(unique_documents) + ".",
            "",
            "Please verify final eligibility, official dates, and application rules from the official notification before applying.",
        ]
    )

    return "\n".join(lines)


def answer_question(profile, query, exams, schemes, jobs=None, history=None):
    query = normalize_text(query)

    if not query:
        return {
            "answer": "Ask me about eligible schemes, exams, documents, deadlines, or application steps.",
            "provider": "local",
            "items": [],
        }

    relevant = retrieve_relevant_items(profile, query, exams, schemes, jobs)
    context_items = [
        serialize_item(item, item_type, profile)
        for item_type, item in relevant
    ]

    prompt = build_prompt(profile, query, context_items, history)
    llm_answer, llm_error = call_openai_llm(prompt)

    if llm_answer:
        answer = llm_answer
        provider = "openai-rag"
    else:
        answer = local_grounded_answer(query, context_items, profile)
        provider = "local-semantic-rag"

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
            "compensation": (
                item.compensation_summary
                if item_type == "job"
                else ""
            ),
            "registration_window": (
                item.registration_window
                if item_type == "job"
                else ""
            ),
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
