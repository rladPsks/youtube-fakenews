import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"

GB_MODEL_PATH = MODEL_DIR / "gradient_boosting_2feat_model.pkl"
VECTORIZER_PATH = MODEL_DIR / "tfidf_vectorizer.pkl"
TAU_PATH = MODEL_DIR / "tau_by_alpha.json"

gb_model = joblib.load(GB_MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

with open(TAU_PATH, "r", encoding="utf-8") as f:
    TAU_BY_ALPHA = json.load(f)


def safe_entropy(p0, p1):
    ps = [p for p in [p0, p1] if pd.notna(p) and p > 0]
    return -sum(p * np.log(p) for p in ps)


def compute_tfidf_reason_mean(reasons):
    reasons = [
        str(r).strip()
        for r in reasons
        if str(r).strip()
    ]

    if len(reasons) < 2:
        return np.nan

    mat = vectorizer.transform(reasons)
    sim = cosine_similarity(mat)
    upper = sim[np.triu_indices_from(sim, k=1)]

    return float(np.mean(upper))


def compute_facttest_features(qwen_outputs):
    answers = [
        item.get("answer")
        for item in qwen_outputs
        if item.get("answer") in [0, 1]
    ]

    reasons = [
        item.get("reason", "")
        for item in qwen_outputs
        if item.get("reason", "")
    ]

    valid_n = len(answers)

    if valid_n == 0:
        return {
            "answer_entropy": np.nan,
            "tfidf_reason_mean": np.nan,
        }

    vote_0 = sum(a == 0 for a in answers)
    vote_1 = sum(a == 1 for a in answers)

    p0 = vote_0 / valid_n
    p1 = vote_1 / valid_n

    return {
        "answer_entropy": safe_entropy(p0, p1),
        "tfidf_reason_mean": compute_tfidf_reason_mean(reasons),
    }


def compute_score_from_qwen_outputs(qwen_outputs):
    feat = compute_facttest_features(qwen_outputs)

    X = pd.DataFrame([{
        "answer_entropy": feat["answer_entropy"],
        "tfidf_reason_mean": feat["tfidf_reason_mean"],
    }])

    score = gb_model.predict_proba(X)[:, 1][0]

    return float(score), feat


def apply_facttest_by_alpha(qwen_outputs):
    score, feat = compute_score_from_qwen_outputs(qwen_outputs)

    results = []

    for alpha_str, tau in TAU_BY_ALPHA.items():
        alpha = float(alpha_str)
        tau = float(tau)

        accepted = score > tau

        results.append({
            "alpha": alpha,
            "tau": round(tau, 6),
            "score": round(score, 6),
            "accepted": bool(accepted),
            "decision": "ACCEPT" if accepted else "ABSTAIN",
        })

    results = sorted(results, key=lambda x: x["alpha"])

    facttest_features = {
        "answer_entropy": None if pd.isna(feat["answer_entropy"]) else round(float(feat["answer_entropy"]), 6),
        "tfidf_reason_mean": None if pd.isna(feat["tfidf_reason_mean"]) else round(float(feat["tfidf_reason_mean"]), 6),
        "facttest_score": round(float(score), 6),
    }

    return results, facttest_features