# services.py
from typing import List, Dict, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv
import os
import models, schemas

# ---- Load .env once (for OPENAI_API_KEY) ----
load_dotenv()

# ---- GPT-4o client (optional: only used when generating care plans) ----
try:
    from openai import OpenAI
    _openai_client = OpenAI()  # uses OPENAI_API_KEY from env
except Exception:
    _openai_client = None  # we’ll handle missing client gracefully


# ---------- Helpers ----------
def _get_breed_by_name_or_404(db: Session, breed_name: str) -> models.Breed:
    breed = db.query(models.Breed).filter(models.Breed.name == breed_name).first()
    if not breed:
        # suggest the closest match
        all_names = [b.name for b in db.query(models.Breed.name).all()]
        import difflib
        suggestion = difflib.get_close_matches(breed_name, all_names, n=1)
        msg = f"Breed '{breed_name}' not found."
        if suggestion:
            msg += f" Did you mean '{suggestion[0]}'?"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    return breed


def _fetch_target_diseases(db: Session, breed_id: int) -> List[Tuple[str, float, int]]:
    """
    Returns list of (disease_name, prevalence, disease_id) for the target breed.
    """
    q = (
        db.query(models.Disease.name, models.BreedDiseaseLink.prevalence, models.Disease.id)
        .join(models.BreedDiseaseLink, models.Disease.id == models.BreedDiseaseLink.disease_id)
        .filter(models.BreedDiseaseLink.breed_id == breed_id)
    )
    return [(name, prev, did) for (name, prev, did) in q.all()]


def _top_similar_breeds_via_sql(db: Session, target_breed_name: str) -> List[Tuple[str, str, float]]:
    """
    Uses a SQL query (close to the one given in the assignment) to compute Jaccard similarity
    on shared diseases. Returns up to 3 rows: (name, species, similarity_raw).
    """
    sql = text(
        """
        SELECT b2.name AS name, b2.species AS species,
               (SELECT COUNT(*)
                FROM breed_disease_links l1
                INNER JOIN breed_disease_links l2 ON l1.disease_id = l2.disease_id
                WHERE l1.breed_id = b1.id AND l2.breed_id = b2.id) * 1.0 /
               (SELECT COUNT(DISTINCT disease_id)
                FROM breed_disease_links l
                WHERE l.breed_id IN (b1.id, b2.id)) AS similarity
        FROM breeds b1, breeds b2
        WHERE b1.name = :target_breed AND b2.name != :target_breed
        ORDER BY similarity DESC
        LIMIT 3;
        """
    )
    rows = db.execute(sql, {"target_breed": target_breed_name}).fetchall()
    # rows -> List[Row(name, species, similarity)]
    return [(r.name, r.species, float(r.similarity) if r.similarity is not None else 0.0) for r in rows]


def _apply_species_penalty(db: Session, target_species: str, sims: List[Tuple[str, str, float]]) -> List[Tuple[str, str, float]]:
    """
    If species differs, subtract 0.1; clamp to [0,1].
    """
    adjusted = []
    for (name, species, sim) in sims:
        score = sim
        if species != target_species:
            score = max(0.0, sim - 0.1)
        adjusted.append((name, species, round(score, 4)))
    # keep order by score desc
    adjusted.sort(key=lambda x: x[2], reverse=True)
    return adjusted


def _shared_diseases_with_top_breeds(
    db: Session,
    target_disease_ids: List[int],
    top_breed_names: List[str]
) -> List[str]:
    """
    Returns the union of disease names shared between the target and any of the top similar breeds.
    """
    if not top_breed_names:
        return []

    # get disease ids for each similar breed, take intersection with target, collect names
    target_set = set(target_disease_ids)
    shared_ids = set()

    # map disease_id -> name
    disease_map = {d.id: d.name for d in db.query(models.Disease).all()}

    for bname in top_breed_names:
        b = db.query(models.Breed).filter(models.Breed.name == bname).first()
        if not b:
            continue
        their_ids = {
            did for (did,) in db.query(models.BreedDiseaseLink.disease_id)
            .filter(models.BreedDiseaseLink.breed_id == b.id).all()
        }
        shared_ids |= (their_ids & target_set)

    return sorted([disease_map[did] for did in shared_ids])


def _generate_care_plan(breed_name: str, diseases_with_prev: List[Tuple[str, float]]) -> str:
    if not _openai_client or not os.getenv("OPENAI_API_KEY"):
        return _fallback_plan(breed_name, diseases_with_prev)
    try:
        # OpenAI call...
        resp = _openai_client.chat.completions.create(...)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        # Fallback if API quota error or any failure
        return _fallback_plan(breed_name, diseases_with_prev)

def _fallback_plan(breed_name, diseases):
    bullets = [f"- {name}: monitor, vet checkups, lifestyle adjustments." for (name, _prev) in diseases]
    return f"Preventive care plan for {breed_name}:\n" + "\n".join(bullets)




# ---------- Public service ----------
def run_risk_analysis(db: Session, breed_name: str) -> schemas.RiskAnalysisResponseSchema:
    # 1) Validate + get target breed
    target = _get_breed_by_name_or_404(db, breed_name)

    # 2) Get target diseases
    target_diseases = _fetch_target_diseases(db, target.id)  # [(name, prevalence, id), ...]
    target_disease_ids = [did for (_n, _p, did) in target_diseases]

    # 3) Similarity (raw SQL) + apply species penalty
    top_raw = _top_similar_breeds_via_sql(db, target.name)              # [(name, species, sim), ...]
    top_adj = _apply_species_penalty(db, target.species, top_raw)       # penalized & sorted

    # 4) Shared diseases (union across top similar breeds)
    top_names = [t[0] for t in top_adj]
    shared = _shared_diseases_with_top_breeds(db, target_disease_ids, top_names)

    # 5) Care plan via GPT-4o (or fallback)
    care_plan = _generate_care_plan(target.name, [(n, p) for (n, p, _id) in target_diseases])

    # 6) Build response
    return schemas.RiskAnalysisResponseSchema(
        target_breed=target.name,
        similar_breeds=[
            schemas.SimilarBreedSchema(name=name, species=species, similarity=score)
            for (name, species, score) in top_adj
        ],
        shared_diseases=shared,
        care_plan=care_plan
    )
