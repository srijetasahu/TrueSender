"""
main.py
--------
TrueSender - FastAPI service combining both detection techniques:
    1. ML classifier (word+char TF-IDF -> voting ensemble)  -> spam/ham + confidence band
    2. Rule-based phishing heuristics (app/phishing_rules.py) -> phishing risk

Exposes:
    GET  /health   - liveness check, reports whether the model is loaded
    POST /classify - ML-only spam/ham classification
    POST /analyze  - COMBINED result: this is the endpoint the Java backend calls

Run:
    uvicorn main:app --reload --port 8000

Test directly (without Java) at: http://127.0.0.1:8000/docs
"""

import re
import string
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from scipy.sparse import hstack

from app.phishing_rules import analyze_phishing

MODEL_PATH = "models/spam_classifier.joblib"
WORD_VECTORIZER_PATH = "models/tfidf_word_vectorizer.joblib"
CHAR_VECTORIZER_PATH = "models/tfidf_char_vectorizer.joblib"

app = FastAPI(title="TrueSender ML Service", version="1.0.0")

# Loaded once at startup, reused for every request (fast inference).
try:
    model = joblib.load(MODEL_PATH)
    word_vectorizer = joblib.load(WORD_VECTORIZER_PATH)
    char_vectorizer = joblib.load(CHAR_VECTORIZER_PATH)
    print("Model and vectorizers loaded successfully.")
except FileNotFoundError:
    model = None
    word_vectorizer = None
    char_vectorizer = None
    print("WARNING: Model files not found. Run 'python train_model.py' first.")


def clean_text(text: str) -> str:
    """Must be identical to the cleaning function in train_model.py."""
    text = text.lower()
    text = re.sub(r"http\S+|www\.\S+", " URL ", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def confidence_band(spam_prob: float) -> tuple[str, str]:
    """
    Maps a spam probability to (label, band) per the handover spec:
        spam_prob >= 0.85 -> label=spam,      band=HIGH CONFIDENCE
        spam_prob >= 0.60 -> label=spam,      band=LOW CONFIDENCE
        spam_prob >= 0.40 -> label=uncertain, band=REVIEW MANUALLY
        spam_prob <  0.40 -> label=ham,       band=HIGH CONFIDENCE
    """
    if spam_prob >= 0.85:
        return "spam", "HIGH CONFIDENCE"
    if spam_prob >= 0.60:
        return "spam", "LOW CONFIDENCE"
    if spam_prob >= 0.40:
        return "uncertain", "REVIEW MANUALLY"
    return "ham", "HIGH CONFIDENCE"


def run_ml_classification(text: str) -> dict:
    if model is None or word_vectorizer is None or char_vectorizer is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run 'python train_model.py' first.",
        )

    cleaned = clean_text(text)
    word_vec = word_vectorizer.transform([cleaned])
    char_vec = char_vectorizer.transform([cleaned])
    combined_vec = hstack([word_vec, char_vec]).tocsr()

    probs = model.predict_proba(combined_vec)[0]  # [P(ham), P(spam)]
    ham_prob, spam_prob = float(probs[0]), float(probs[1])

    label, band = confidence_band(spam_prob)
    confidence = max(spam_prob, ham_prob)

    return {
        "label": label,
        "confidence": confidence,
        "confidence_band": band,
        "spam_probability": spam_prob,
        "ham_probability": ham_prob,
    }


# ---------------------------------------------------------------------------
# Pydantic request/response schemas
# ---------------------------------------------------------------------------
class EmailRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw email text to classify")


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw email text/body")
    sender_display_name: str = Field("", description="e.g. 'PayPal Support'")
    sender_email: str = Field("", description="e.g. support@paypa1-secure.ru")


class ClassificationResponse(BaseModel):
    label: str            # "spam", "ham", or "uncertain"
    confidence: float      # 0.0 - 1.0
    confidence_band: str   # HIGH CONFIDENCE / LOW CONFIDENCE / REVIEW MANUALLY
    spam_probability: float
    ham_probability: float


class AnalyzeResponse(BaseModel):
    ml_result: ClassificationResponse
    phishing_suspected: bool
    phishing_risk_score: float
    phishing_triggered_checks: int
    phishing_total_checks: int
    phishing_details: dict
    final_verdict: str  # SAFE / SPAM / SUSPICIOUS / HIGH RISK


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model is not None
        and word_vectorizer is not None
        and char_vectorizer is not None,
    }


@app.post("/classify", response_model=ClassificationResponse)
def classify(request: EmailRequest):
    """ML-only endpoint, useful for testing/demoing Member 1's piece in isolation."""
    result = run_ml_classification(request.text)
    return ClassificationResponse(**result)


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    """
    Combined endpoint: runs BOTH detection techniques and merges them into
    one of four verdicts (per handover Section 2):
        SAFE       - ML says ham AND phishing not suspected
        SPAM       - ML says spam BUT phishing not suspected
        SUSPICIOUS - ML says ham BUT phishing suspected (2+ checks)
        HIGH RISK  - ML says spam AND phishing suspected
    This is the main endpoint the Java backend calls.
    """
    ml_result = run_ml_classification(request.text)
    phishing_result = analyze_phishing(
        request.text, request.sender_display_name, request.sender_email
    )

    ml_says_spam = ml_result["label"] == "spam"
    phishing_flag = phishing_result["is_phishing_suspected"]

    if ml_says_spam and phishing_flag:
        verdict = "HIGH RISK"
    elif ml_says_spam:
        verdict = "SPAM"
    elif phishing_flag:
        verdict = "SUSPICIOUS"
    else:
        verdict = "SAFE"

    return AnalyzeResponse(
        ml_result=ClassificationResponse(**ml_result),
        phishing_suspected=phishing_result["is_phishing_suspected"],
        phishing_risk_score=phishing_result["risk_score"],
        phishing_triggered_checks=phishing_result["triggered_checks"],
        phishing_total_checks=phishing_result["total_checks"],
        phishing_details=phishing_result["checks"],
        final_verdict=verdict,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
