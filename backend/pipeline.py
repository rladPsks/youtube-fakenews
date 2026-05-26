import math

from youtube_utils import extract_video_id, get_transcript
from qwen_inference import run_qwen_7_samples
from facttest import apply_facttest_by_alpha


def compute_features(labels):
    p1 = sum(labels) / len(labels)
    p0 = 1 - p1

    pred = 1 if p1 >= p0 else 0
    confidence = max(p0, p1)
    margin = abs(p1 - p0)

    eps = 1e-12
    entropy = -(p0 * math.log(p0 + eps) + p1 * math.log(p1 + eps))

    return {
        "p0": round(p0, 4),
        "p1": round(p1, 4),
        "pred": pred,
        "confidence": round(confidence, 4),
        "margin": round(margin, 4),
        "entropy": round(entropy, 4),
    }


def select_representative_reason(labels, reasons, pred):
    pred_reasons = [
        reason for label, reason in zip(labels, reasons)
        if label == pred and reason
    ]

    return pred_reasons[0] if pred_reasons else reasons[0]


def analyze_video(url: str):
    video_id = extract_video_id(url)
    transcript = get_transcript(video_id)

    qwen_outputs = run_qwen_7_samples(
        title="",
        transcript=transcript,
    )

    labels = [item["label"] for item in qwen_outputs]
    reasons = [item["reason"] for item in qwen_outputs]

    features = compute_features(labels)
    pred = features["pred"]

    representative_reason = select_representative_reason(
        labels,
        reasons,
        pred,
    )

    facttest_results, facttest_features = apply_facttest_by_alpha(qwen_outputs)

    return {
        "url": url,
        "video_id": video_id,
        "prediction": "FAKE" if pred == 1 else "REAL",
        "representative_reason": representative_reason,
        "p0": features["p0"],
        "p1": features["p1"],
        "confidence": features["confidence"],
        "margin": features["margin"],
        "entropy": features["entropy"],
        "facttest": facttest_results,
        "facttest_features": facttest_features,
        "all_outputs": qwen_outputs,
        "transcript_preview": transcript[:1000],
    }