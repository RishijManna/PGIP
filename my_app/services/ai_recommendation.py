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
        for item in text.split(",")
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
            scheme.additional_info,
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

    if getattr(item, "date", None) and item.date >= date.today():
        score += 0.04
        reasons.append("upcoming")

    return score, reasons


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
    item.ai_reasons = reasons[:3] or ["profile similarity"]
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
