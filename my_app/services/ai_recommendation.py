def safe_split(text):
    if not text:
        return []

    return [
        i.strip().lower()
        for i in text.split(",")
        if i.strip()
    ]


def text_match(a, b):

    if not a or not b:
        return 0

    a = a.lower()
    b = b.lower()

    if a in b or b in a:
        return 1

    return 0


def interest_score(interests, category):

    score = 0

    if not category:
        return score

    category = category.lower()

    for interest in interests:

        if interest in category:
            score += 2

    return score


def calculate_exam_score(profile, exam):

    score = 0

    interests = safe_split(
        profile.interests
    )

    score += interest_score(
        interests,
        exam.category
    )

    score += text_match(
        profile.location,
        exam.location
    )

    score += text_match(
        profile.education,
        exam.e_eligibility
    )

    return score


def calculate_scheme_score(profile, scheme):

    score = 0

    interests = safe_split(
        profile.interests
    )

    score += interest_score(
        interests,
        scheme.category
    )

    score += text_match(
        profile.location,
        scheme.location
    )

    score += text_match(
        profile.education,
        scheme.s_eligibility
    )

    return score


def recommend_exams(profile, exams):

    scored = []

    for exam in exams:

        score = calculate_exam_score(
            profile,
            exam
        )

        scored.append(
            (exam, score)
        )

    scored.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return [
        exam
        for exam, score in scored
        if score > 0
    ][:15]


def recommend_schemes(profile, schemes):

    scored = []

    for scheme in schemes:

        score = calculate_scheme_score(
            profile,
            scheme
        )

        scored.append(
            (scheme, score)
        )

    scored.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return [
        scheme
        for scheme, score in scored
        if score > 0
    ][:15]