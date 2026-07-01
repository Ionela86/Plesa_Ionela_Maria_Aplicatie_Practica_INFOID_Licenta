"""Modul AI gratuit/local pentru SMART-RECRUT.

Nu folosește servicii plătite și nu cere chei API. Dacă există instalate
sentence-transformers / transformers, le folosește local. Altfel folosește
un fallback rapid pe similaritate lexicală, ca aplicația să pornească stabil.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache
from typing import Iterable

_WORD_RE = re.compile(r"[a-zăâîșşțţ0-9+#.]+", re.IGNORECASE)


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _WORD_RE.findall(text or "") if len(t) > 1]


def _cosine_counter(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[k] * b[k] for k in common)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@lru_cache(maxsize=1)
def _load_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


@lru_cache(maxsize=1)
def _load_summarizer():
    try:
        from transformers import pipeline
        return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    except Exception:
        return None


def semantic_match(job_text: str, cv_text: str) -> int:
    """Returnează un scor AI 0-100 între cerințele jobului și CV."""
    job_text = (job_text or "").strip()
    cv_text = (cv_text or "").strip()
    if not job_text or not cv_text:
        return 0

    model = _load_embedding_model()
    if model is not None:
        try:
            embeddings = model.encode([job_text, cv_text])
            a, b = embeddings[0], embeddings[1]
            dot = float(sum(x * y for x, y in zip(a, b)))
            norm_a = math.sqrt(float(sum(x * x for x in a)))
            norm_b = math.sqrt(float(sum(y * y for y in b)))
            return int(max(0, min(100, (dot / (norm_a * norm_b)) * 100))) if norm_a and norm_b else 0
        except Exception:
            pass

    return int(max(0, min(100, _cosine_counter(Counter(_tokens(job_text)), Counter(_tokens(cv_text))) * 100)))


def generate_summary(text: str) -> str:
    """Generează un rezumat scurt al CV-ului. Fallback-ul e gratuit și offline."""
    clean = " ".join((text or "").split())
    if not clean:
        return "Nu s-a putut extrage text din CV."

    summarizer = _load_summarizer()
    if summarizer is not None and len(clean.split()) > 80:
        try:
            result = summarizer(clean[:2500], max_length=70, min_length=25, do_sample=False)
            return result[0].get("summary_text", "").strip() or _fallback_summary(clean)
        except Exception:
            pass

    return _fallback_summary(clean)


def _fallback_summary(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    picked = [s.strip() for s in sentences if len(s.strip()) > 40][:3]
    if picked:
        return " ".join(picked)[:500]
    return text[:500]


def generate_cv_opinion(text: str, score: int = 0, job_text: str = "", skills: list[str] | None = None) -> str:
    """O parere despre calitatea CV-ului, nu o reluare a studiilor/experientei."""
    clean = " ".join((text or "").split())
    lower = clean.lower()
    skills = skills or []

    if not clean:
        return "CV-ul nu poate fi evaluat corect deoarece nu s-a putut extrage textul din document. Recomand verificarea formatului PDF/DOCX."

    observations = []
    if len(clean) < 900:
        observations.append("CV-ul pare destul de scurt si ar merita completat cu rezultate concrete si responsabilitati mai clare")
    else:
        observations.append("CV-ul ofera suficienta informatie pentru o prima triere")

    has_contact = any(x in lower for x in ["@", "telefon", "phone", "email", "+40", "linkedin"])
    if has_contact:
        observations.append("datele de contact par usor de identificat")
    else:
        observations.append("datele de contact nu sunt evidente si ar trebui facute mai vizibile")

    if skills:
        observations.append("competentele sunt vizibile, dar ar fi mai convingatoare daca sunt sustinute prin exemple masurabile")
    else:
        observations.append("competentele-cheie nu ies suficient in evidenta")

    if score >= 70:
        return "Candidatul prezintă un CV bine organizat și ușor de parcurs. Informațiile sunt structurate logic, iar experiența este descrisă clar. Documentul transmite profesionalism și oferă suficiente detalii pentru evaluarea inițială."
    elif score >= 45:
        return "CV-ul este suficient de clar pentru o primă evaluare, dar ar merita verificate anumite detalii în interviu. Structura documentului permite identificarea rapidă a informațiilor importante, însă unele competențe ar putea fi prezentate mai convingător."
    else:
        return "CV-ul nu este suficient de convingător pentru cerințele introduse. Recomand verificarea structurii, completarea competențelor relevante și clarificarea rezultatelor obținute în rolurile anterioare."


def generate_recruitment_suggestion(score: int, years: int, min_y: int, title_match: int, keyword_match: int, ai_score: int,
                                    job_title: str = "", context_q: str = "", skills: list[str] | None = None) -> str:
    """Sugestie pentru recrutor dupa compararea CV-ului cu cerintele postului."""
    skills = skills or []
    weak = []
    if min_y and years < min_y:
        weak.append("vechimea pare sub nivelul cerut")
    if title_match < 30 and job_title:
        weak.append("titlul/profilul nu se aliniază clar cu postul")
    if keyword_match < 35 and context_q:
        weak.append("cerintele postului nu apar suficient in CV")
    if ai_score < 35 and (job_title or context_q):
        weak.append("potrivirea semantica este slaba")

    if score >= 70:
        return "Cerințele postului privind experiența în managementul proiectelor și coordonarea echipelor sunt acoperite în mare măsură. Se recomandă programarea unui interviu pentru validarea competențelor tehnice și a compatibilității cu cultura organizațională."
    if score >= 50:
        return "Se recomandă o discuție scurtă de preselectie. Candidatul poate fi potrivit, dar este utilă validarea cerințelor obligatorii ale postului și a compatibilității cu echipa."
    if score >= 30:
        details = ", ".join(weak[:2]) if weak else "exista diferente intre CV si cerintele postului"
        return f"Sugerez pastrarea candidatului ca rezerva sau solicitarea unor clarificari, deoarece {details}."
    details = ", ".join(weak[:2]) if weak else "potrivirea cu rolul este redusa"
    return f"Sugerez respingerea pentru acest rol sau redirectionarea spre un post mai potrivit, deoarece {details}."
