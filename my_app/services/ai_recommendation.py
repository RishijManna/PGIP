from datetime import date

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:  # pragma: no cover - used only when deployment deps are missing
    TfidfVectorizer = None
    cosine_similarity = None


MAX_RESULTS = 15


INTEREST_KEYWORDS = {
    "tech": "technology engineering software computer science digital innovation",
    "govt": "government public services welfare central state scheme",
    "exams": "competitive exams entrance test recruitment admission",
    "health": "health medical insurance wellness hospital healthcare",
    "env": "environment climate sustainability coastal agriculture ecology",
    "startup": "startup entrepreneurship business loan subsidy incubation",
    "finance": "finance tax banking income savings pension insurance",
    "jobs": "employment job recruitment government vacancy training",
    "edu": "education scholarship higher education college university",
    "scholarships": "scholarship education students fee support financial aid",
    "welfare": "welfare support assistance citizens rural low income",
}

EDUCATION_KEYWORDS = {
    "High School": "10th pass school secondary",
    "Diploma": "diploma technical vocational",
    "Undergraduate": "12th pass undergraduate college bachelor",
    "Postgraduate": "graduate postgraduate masters post graduate",
    "PhD": "postgraduate phd research doctorate",
}

INCOME_KEYWORDS = {
    "<1 Lakh": "low income bpl financial assistance subsidy welfare",
    "1-3 Lakhs": "low income financial assistance subsidy welfare",
    "3-5 Lakhs": "middle income support loan subsidy",
    "5-10 Lakhs": "middle income loan tax finance",
    ">10 Lakhs": "tax finance entrepreneurship investment",
}


def safe_split(text):
    if not text:
        return []

    return [
        item.strip()
        for item in str(text).replace("\n", ",").split(",")
        if item.strip()
    ]


def normalize(text):
    return str(text or "").strip().lower()


def contains_match(left, right):
    left = normalize(left)
    right = normalize(right)

    if not left or not right:
        return False

    return left in right or right in left


def age_from_dob(dob):
    if not dob:
        return None

    today = date.today()
    return (
        today.year
        - dob.year
        - ((today.month, today.day) < (dob.month, dob.day))
    )


def profile_to_document(profile):
    interests = safe_split(profile.interests)
    expanded_interests = [
        INTEREST_KEYWORDS.get(interest, interest)
        for interest in interests
    ]

    parts = [
        profile.education,
        EDUCATION_KEYWORDS.get(profile.education, ""),
        profile.income,
        INCOME_KEYWORDS.get(profile.income, ""),
        profile.location,
        profile.nation,
        profile.religion,
        profile.caste,
        profile.gender,
        profile.skills,
        profile.class_10_percentage,
        profile.class_12_percentage,
        profile.graduation_cgpa,
        profile.semester_marks,
        " ".join(expanded_interests),
    ]

    return " ".join(str(part or "") for part in parts)


def exam_to_document(exam):
    return " ".join(
        str(part or "")
        for part in [
            exam.name,
            exam.exam_type,
            exam.category,
            exam.location,
            exam.mode,
            exam.e_eligibility,
            getattr(exam, "conducting_body", ""),
            getattr(exam, "application_fee", ""),
            getattr(exam, "salary_package", ""),
            getattr(exam, "required_skills", ""),
            getattr(exam, "registration_window", ""),
            exam.additional_info,
        ]
    )


def scheme_to_document(scheme):
    return " ".join(
        str(part or "")
        for part in [
            scheme.name,
            scheme.scheme_type,
            scheme.category,
            scheme.location,
            scheme.s_eligibility,
            scheme.description,
            scheme.benefits,
            getattr(scheme, "benefit_amount", ""),
            getattr(scheme, "required_documents", ""),
            getattr(scheme, "registration_window", ""),
            scheme.additional_info,
        ]
    )


def job_to_document(job):
    return " ".join(
        str(part or "")
        for part in [
            job.title,
            job.company_or_org,
            job.opportunity_type,
            job.sector,
            job.location,
            job.qualification,
            job.required_skills,
            job.compensation_summary,
            job.registration_window,
            job.description,
            job.source_name,
        ]
    )


def calculate_signal_boosts(profile, item, item_type):
    score = 0.0
    reasons = []

    if contains_match(profile.location, getattr(item, "location", "")):
        score += 0.18
        reasons.append("location match")
    elif normalize(getattr(item, "location", "")) in {"all india", "multiple cities"}:
        score += 0.08
        reasons.append("available broadly")

    if item_type == "job":
        eligibility = getattr(item, "qualification", "")
    else:
        eligibility = getattr(
            item,
            "e_eligibility" if item_type == "exam" else "s_eligibility",
            "",
        )

    if education_matches(profile.education, eligibility):
        score += 0.16
        reasons.append("education eligibility match")

    if interest_matches(profile.interests, getattr(item, "category", "")):
        score += 0.20
        reasons.append("interest/category match")

    if item_type == "job":
        skill_score, skill_reasons = job_skill_and_marks_boost(profile, item)
        score += skill_score
        reasons.extend(skill_reasons)

    item_date = (
        getattr(item, "effective_deadline", None)
        or getattr(item, "date", None)
        or getattr(item, "deadline", None)
    )
    if item_date and item_date >= date.today():
        score += 0.04
        reasons.append("upcoming")

    return score, reasons


def job_skill_and_marks_boost(profile, job):
    score = 0.0
    reasons = []

    profile_skills = {
        normalize(skill)
        for skill in safe_split(getattr(profile, "skills", ""))
    }
    required_skills = {
        normalize(skill)
        for skill in safe_split(getattr(job, "required_skills", ""))
    }

    if profile_skills and required_skills:
        overlap = profile_skills & required_skills

        if overlap:
            score += min(0.20, 0.06 * len(overlap))
            reasons.append("skill match: " + ", ".join(sorted(overlap)[:3]))

    if marks_meet_requirement(
        profile.class_10_percentage,
        job.min_10th_percentage,
    ):
        score += 0.05
        reasons.append("10th marks eligible")

    if marks_meet_requirement(
        profile.class_12_percentage,
        job.min_12th_percentage,
    ):
        score += 0.05
        reasons.append("12th marks eligible")

    if marks_meet_requirement(profile.graduation_cgpa, job.min_cgpa):
        score += 0.08
        reasons.append("CGPA eligible")

    return score, reasons


def marks_meet_requirement(profile_value, required_value):
    if profile_value is None or required_value is None:
        return False

    return profile_value >= required_value


def income_matches(profile_income, text):
    income = normalize(profile_income)
    text = normalize(text)

    if not income or not text:
        return False

    low_income_terms = ["bpl", "low income", "financial assistance", "subsidy"]
    middle_income_terms = ["middle income", "loan", "tax", "finance"]

    if income in {"<1 lakh", "1-3 lakhs"}:
        return any(term in text for term in low_income_terms)

    if income in {"3-5 lakhs", "5-10 lakhs"}:
        return any(term in text for term in middle_income_terms)

    return any(term in text for term in ["tax", "investment", "entrepreneurship"])


def gender_or_caste_matches(profile, text):
    text = normalize(text)
    matches = []

    if profile.gender and normalize(profile.gender) in text:
        matches.append("gender-specific eligibility match")

    if normalize(profile.gender) == "female" and any(
        term in text for term in ["women", "woman", "girl", "girls", "female"]
    ):
        matches.append("women/girl student eligibility match")

    if profile.caste and normalize(profile.caste) in text:
        matches.append("caste/category eligibility match")

    return matches


def profile_missing_fields(profile):
    fields = [
        ("education", "education"),
        ("income", "income range"),
        ("location", "location/state"),
        ("dob", "date of birth"),
        ("gender", "gender"),
        ("caste", "caste/category"),
        ("interests", "interests"),
    ]

    return [
        label
        for attr, label in fields
        if not getattr(profile, attr, None)
    ]


def suggested_documents_for(item, item_type):
    text = normalize(
        " ".join(
            str(part or "")
            for part in [
                getattr(item, "name", getattr(item, "title", "")),
                getattr(item, "category", getattr(item, "sector", "")),
                item.location,
                getattr(item, "e_eligibility", ""),
                getattr(item, "s_eligibility", ""),
                getattr(item, "description", ""),
                getattr(item, "benefits", ""),
                getattr(item, "benefit_amount", ""),
                getattr(item, "salary_package", ""),
                getattr(item, "application_fee", ""),
                getattr(item, "qualification", ""),
                getattr(item, "required_skills", ""),
                getattr(item, "required_documents", ""),
                getattr(item, "additional_info", ""),
            ]
        )
    )

    documents = [
        "Aadhaar or government ID",
        "Passport-size photograph",
        "Address or domicile proof",
    ]

    if item_type in {"exam", "job"} or any(
        term in text for term in ["education", "student", "scholarship", "12th", "graduate"]
    ):
        documents.append("Latest marksheet or education certificate")

    if item_type == "job":
        documents.append("Updated resume")

    if any(term in text for term in ["income", "bpl", "financial", "subsidy", "fee"]):
        documents.append("Income certificate")

    if any(term in text for term in ["sc", "st", "obc", "caste"]):
        documents.append("Caste/category certificate")

    if any(term in text for term in ["bank", "loan", "pension", "benefit", "financial"]):
        documents.append("Bank account details")

    return documents


def build_eligibility_explanation(profile, item, item_type):
    if item_type == "job":
        eligibility = getattr(item, "qualification", "")
    else:
        eligibility = getattr(
            item,
            "e_eligibility" if item_type == "exam" else "s_eligibility",
            "",
        )
    item_text = " ".join(
        str(part or "")
        for part in [
            getattr(item, "name", getattr(item, "title", "")),
            getattr(item, "category", getattr(item, "sector", "")),
            item.location,
            eligibility,
            getattr(item, "description", ""),
            getattr(item, "benefits", ""),
            getattr(item, "required_skills", ""),
            getattr(item, "additional_info", ""),
        ]
    )

    matches = []
    concerns = []
    score = 36

    if contains_match(profile.location, getattr(item, "location", "")):
        matches.append(f"Your location matches {item.location}.")
        score += 18
    elif normalize(getattr(item, "location", "")) in {"all india", "multiple cities"}:
        item_name = getattr(item, "name", getattr(item, "title", "This opportunity"))
        matches.append(f"{item_name} is available broadly across India.")
        score += 12
    elif profile.location:
        concerns.append(f"Your location is {profile.location}, while this lists {item.location}.")

    if education_matches(profile.education, eligibility):
        matches.append(f"Your education level fits the listed eligibility: {eligibility}.")
        score += 18
    elif eligibility and normalize(eligibility) == "open to all":
        matches.append("The listed eligibility is open to all.")
        score += 12
    elif profile.education and eligibility:
        concerns.append(f"Check education carefully: your profile says {profile.education}, eligibility says {eligibility}.")

    if interest_matches(profile.interests, getattr(item, "category", "")):
        matches.append(f"Your interests align with the {item.category} category.")
        score += 14

    if income_matches(profile.income, item_text):
        matches.append("Your income range appears relevant to the listed benefits or eligibility.")
        score += 10

    if item_type == "job":
        job_score, job_reasons = job_skill_and_marks_boost(profile, item)
        matches.extend(job_reasons)
        score += int(job_score * 100)

    demographic_matches = gender_or_caste_matches(profile, item_text)
    if demographic_matches:
        matches.extend(demographic_matches)
        score += min(len(demographic_matches) * 8, 16)

    item_date = (
        getattr(item, "effective_deadline", None)
        or getattr(item, "date", None)
        or getattr(item, "deadline", None)
    )
    if item_date:
        if item_date >= date.today():
            matches.append(f"The deadline/date is upcoming: {item_date}.")
            score += 5
        else:
            concerns.append(f"The listed date {item_date} has already passed.")
            score -= 12

    missing_fields = profile_missing_fields(profile)
    if missing_fields:
        concerns.append(
            "Profile fields missing for stronger eligibility judgement: "
            + ", ".join(missing_fields[:4])
            + "."
        )
        score -= min(len(missing_fields) * 2, 10)

    confidence = max(5, min(score, 98))

    if confidence >= 75:
        verdict = "Strong match"
    elif confidence >= 50:
        verdict = "Possible match"
    else:
        verdict = "Needs review"

    summary = (
        f"{getattr(item, 'name', getattr(item, 'title', 'This opportunity'))} looks like a {verdict.lower()} for your profile based on "
        "the available portal data."
    )

    return {
        "verdict": verdict,
        "confidence": confidence,
        "summary": summary,
        "matching_factors": matches[:5] or [
            "The portal found partial text similarity with your profile."
        ],
        "concerns": concerns[:4],
        "missing_profile_fields": missing_fields,
        "suggested_documents": suggested_documents_for(item, item_type),
        "next_steps": [
            "Verify the official notification before applying.",
            "Update missing profile fields to improve AI recommendations.",
            "Add the deadline to your calendar if you plan to apply.",
        ],
    }


def education_matches(profile_education, eligibility):
    education = normalize(profile_education)
    eligibility = normalize(eligibility)

    if not education or not eligibility:
        return False

    equivalences = {
        "high school": ["10th", "school"],
        "diploma": ["diploma", "12th", "technical"],
        "undergraduate": ["12th", "undergraduate", "graduate", "open to all"],
        "postgraduate": ["graduate", "post graduate", "postgraduate", "masters"],
        "phd": ["graduate", "post graduate", "postgraduate", "phd", "research"],
    }

    return any(
        keyword in eligibility
        for keyword in equivalences.get(education, [education])
    )


def interest_matches(interests_text, category):
    category = normalize(category)

    if not category:
        return False

    for interest in safe_split(interests_text):
        expanded = normalize(INTEREST_KEYWORDS.get(interest, interest))
        words = [normalize(interest), *expanded.split()]

        if any(word and word in category for word in words):
            return True

    return False


def simple_keyword_score(profile, item, item_type):
    boost, reasons = calculate_signal_boosts(profile, item, item_type)
    return boost, reasons


def add_ai_metadata(item, score, reasons):
    item.ai_score = round(min(score, 1.0) * 100)
    item.ai_reasons = reasons[:5] or ["profile similarity"]
    return item


def rank_items(profile, items, item_to_document, item_type):
    items = list(items)

    if not items:
        return []

    profile_document = profile_to_document(profile)
    item_documents = [item_to_document(item) for item in items]

    if TfidfVectorizer is None or cosine_similarity is None:
        scored_items = []

        for item in items:
            score, reasons = simple_keyword_score(profile, item, item_type)
            scored_items.append((item, score, reasons))

        return finalize_ranked_items(scored_items)

    documents = [profile_document, *item_documents]
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(documents)
    similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()

    scored_items = []

    for item, similarity in zip(items, similarities):
        boost, reasons = calculate_signal_boosts(profile, item, item_type)
        score = (float(similarity) * 0.62) + boost

        if similarity > 0:
            reasons.insert(0, "AI text similarity")

        scored_items.append((item, score, reasons))

    return finalize_ranked_items(scored_items)


def finalize_ranked_items(scored_items):
    scored_items.sort(key=lambda row: row[1], reverse=True)

    ranked = [
        add_ai_metadata(item, score, reasons)
        for item, score, reasons in scored_items
        if score > 0
    ]

    return ranked[:MAX_RESULTS]


def recommend_exams(profile, exams):
    return rank_items(profile, exams, exam_to_document, "exam")


def recommend_schemes(profile, schemes):
    return rank_items(profile, schemes, scheme_to_document, "scheme")


def recommend_jobs(profile, jobs):
    return rank_items(profile, jobs, job_to_document, "job")
