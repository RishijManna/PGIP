import pickle
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

from my_app.models import Exam, JobOpportunity, Scheme
from my_app.services.ai_recommendation import (
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


INDEX_VERSION = 1
INDEX_DIR = Path(settings.BASE_DIR) / "rag_indexes"
INDEX_PATH = INDEX_DIR / "seed_rag_index.pkl"


@dataclass(frozen=True)
class RagRecord:
    item_type: str
    item_id: int
    title: str
    source_name: str
    text: str


def item_title(item, item_type):
    if item_type == "exam":
        return item.name

    if item_type == "scheme":
        return item.name

    return item.title


def item_document(item, item_type):
    if item_type == "exam":
        return exam_to_document(item)

    if item_type == "scheme":
        return scheme_to_document(item)

    return job_to_document(item)


def collect_rag_records():
    rows = []

    for item in Exam.objects.all().iterator():
        rows.append(
            RagRecord(
                item_type="exam",
                item_id=item.id,
                title=item_title(item, "exam"),
                source_name=item.source_name or "Exam database",
                text=item_document(item, "exam"),
            )
        )

    for item in Scheme.objects.all().iterator():
        rows.append(
            RagRecord(
                item_type="scheme",
                item_id=item.id,
                title=item_title(item, "scheme"),
                source_name=item.source_name or "Scheme database",
                text=item_document(item, "scheme"),
            )
        )

    for item in JobOpportunity.objects.all().iterator():
        rows.append(
            RagRecord(
                item_type="job",
                item_id=item.id,
                title=item_title(item, "job"),
                source_name=item.source_name or "Job database",
                text=item_document(item, "job"),
            )
        )

    return rows


def corpus_signature():
    return {
        "exam_count": Exam.objects.count(),
        "scheme_count": Scheme.objects.count(),
        "job_count": JobOpportunity.objects.count(),
        "exam_max_id": Exam.objects.order_by("-id").values_list("id", flat=True).first() or 0,
        "scheme_max_id": Scheme.objects.order_by("-id").values_list("id", flat=True).first() or 0,
        "job_max_id": JobOpportunity.objects.order_by("-id").values_list("id", flat=True).first() or 0,
    }


def build_seed_rag_index(path=INDEX_PATH):
    if TfidfVectorizer is None:
        raise RuntimeError("scikit-learn is required to build the local RAG index.")

    records = collect_rag_records()
    documents = [record.text for record in records]

    if not records:
        raise RuntimeError("No exams, schemes, or jobs exist to index.")

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(documents)

    payload = {
        "version": INDEX_VERSION,
        "signature": corpus_signature(),
        "records": records,
        "vectorizer": vectorizer,
        "matrix": matrix,
    }

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as index_file:
        pickle.dump(payload, index_file)

    return {
        "path": str(path),
        "records": len(records),
        "exams": sum(1 for record in records if record.item_type == "exam"),
        "schemes": sum(1 for record in records if record.item_type == "scheme"),
        "jobs": sum(1 for record in records if record.item_type == "job"),
    }


def load_seed_rag_index(path=INDEX_PATH):
    path = Path(path)

    if not path.exists() or TfidfVectorizer is None or cosine_similarity is None:
        return None

    with path.open("rb") as index_file:
        payload = pickle.load(index_file)

    if payload.get("version") != INDEX_VERSION:
        return None

    if payload.get("signature") != corpus_signature():
        return None

    return payload


def fetch_indexed_items(records):
    ids_by_type = {
        "exam": [],
        "scheme": [],
        "job": [],
    }

    for record in records:
        ids_by_type[record.item_type].append(record.item_id)

    objects_by_key = {}

    for item in Exam.objects.filter(id__in=ids_by_type["exam"]):
        objects_by_key[("exam", item.id)] = item

    for item in Scheme.objects.filter(id__in=ids_by_type["scheme"]):
        objects_by_key[("scheme", item.id)] = item

    for item in JobOpportunity.objects.filter(id__in=ids_by_type["job"]):
        objects_by_key[("job", item.id)] = item

    return objects_by_key


def retrieve_from_seed_rag(profile, query, focus="general", limit=6, path=INDEX_PATH):
    payload = load_seed_rag_index(path)

    if not payload:
        return []

    query_document = f"{query}\n{profile_to_document(profile)}"
    query_matrix = payload["vectorizer"].transform([query_document])
    similarities = cosine_similarity(query_matrix, payload["matrix"]).flatten()
    scored = []

    for score, record in zip(similarities, payload["records"]):
        if focus in {"exam", "scheme", "job"} and record.item_type != focus:
            continue

        scored.append((float(score), record))

    scored.sort(key=lambda row: row[0], reverse=True)
    candidates = [record for score, record in scored if score > 0.01][: limit * 2]
    objects_by_key = fetch_indexed_items(candidates)
    results = []

    for record in candidates:
        item = objects_by_key.get((record.item_type, record.item_id))
        if item:
            results.append((record.item_type, item))

        if len(results) >= limit:
            break

    return results
