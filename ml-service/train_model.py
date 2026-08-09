"""
train_model.py
----------------
TrueSender - ML training script (Member 1's piece), UPDATED with
hyperparameter tuning via GridSearchCV.

WHAT CHANGED FROM THE ORIGINAL VERSION:
    Instead of training each of the 3 algorithms with scikit-learn's default
    settings, GridSearchCV now searches a small grid of hyperparameter values
    for each algorithm and picks the best-performing one, using the same
    5-fold cross-validation already in place. This directly addresses using
    "traditional models" as-is -- the models are now tuned, not left at
    defaults.

Run:
    python train_model.py
"""

import re
import string
import joblib
import numpy as np
import pandas as pd
from scipy.sparse import hstack

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import VotingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

DATA_PATH = "data/emails_merged.csv"
MODEL_PATH = "models/spam_classifier.joblib"
WORD_VECTORIZER_PATH = "models/tfidf_word_vectorizer.joblib"
CHAR_VECTORIZER_PATH = "models/tfidf_char_vectorizer.joblib"


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"http\S+|www\.\S+", " URL ", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tune_naive_bayes(X_train, y_train):
    """Naive Bayes: tune the smoothing parameter alpha."""
    param_grid = {"alpha": [0.01, 0.1, 0.5, 1.0]}
    grid = GridSearchCV(MultinomialNB(), param_grid, cv=5, scoring="accuracy", n_jobs=-1)
    grid.fit(X_train, y_train)
    print(f"  Naive Bayes best params: {grid.best_params_}  best CV accuracy: {grid.best_score_:.4f}")
    return grid.best_estimator_, grid.best_score_


def tune_logistic_regression(X_train, y_train):
    """Logistic Regression: tune regularization strength C."""
    param_grid = {"C": [0.1, 1, 5, 10]}
    grid = GridSearchCV(
        LogisticRegression(max_iter=1000), param_grid, cv=5, scoring="accuracy", n_jobs=-1
    )
    grid.fit(X_train, y_train)
    print(f"  Logistic Regression best params: {grid.best_params_}  best CV accuracy: {grid.best_score_:.4f}")
    return grid.best_estimator_, grid.best_score_


def tune_linear_svm(X_train, y_train):
    """Linear SVM: tune regularization strength C, then calibrate for probabilities."""
    param_grid = {"estimator__C": [0.1, 1, 5, 10]}
    base = CalibratedClassifierCV(LinearSVC(), cv=3)
    grid = GridSearchCV(base, param_grid, cv=5, scoring="accuracy", n_jobs=-1)
    grid.fit(X_train, y_train)
    print(f"  Linear SVM best params: {grid.best_params_}  best CV accuracy: {grid.best_score_:.4f}")
    return grid.best_estimator_, grid.best_score_


def main():
    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["text", "label"])
    print(f"Loaded {len(df)} emails.")
    print(df["label"].value_counts())

    df["clean_text"] = df["text"].apply(clean_text)
    X_text = df["clean_text"]
    y = df["label"].map({"spam": 1, "ham": 0})

    X_train_text, X_test_text, y_train, y_test = train_test_split(
        X_text, y, test_size=0.25, random_state=42, stratify=y
    )

    print("\nVectorizing text (word-level TF-IDF, unigrams + bigrams)...")
    word_vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), analyzer="word")
    X_train_word = word_vectorizer.fit_transform(X_train_text)
    X_test_word = word_vectorizer.transform(X_test_text)

    print("Vectorizing text (char-level TF-IDF, 3-5 grams)...")
    char_vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(3, 5), analyzer="char_wb")
    X_train_char = char_vectorizer.fit_transform(X_train_text)
    X_test_char = char_vectorizer.transform(X_test_text)

    print("Combining word + char features...")
    X_train = hstack([X_train_word, X_train_char]).tocsr()
    X_test = hstack([X_test_word, X_test_char]).tocsr()
    print(f"Combined feature matrix shape: {X_train.shape}")

    # -----------------------------------------------------------------
    # NEW: Hyperparameter tuning for each algorithm, replacing the old
    # "just use default settings" approach. Each tuning function runs
    # its own internal 5-fold cross-validation to pick the best setting.
    # -----------------------------------------------------------------
    print("\nTuning hyperparameters for each algorithm (this takes a few minutes)...")
    print("Tuning Naive Bayes...")
    nb_model, nb_score = tune_naive_bayes(X_train, y_train)

    print("Tuning Logistic Regression...")
    lr_model, lr_score = tune_logistic_regression(X_train, y_train)

    print("Tuning Linear SVM...")
    svm_model, svm_score = tune_linear_svm(X_train, y_train)

    cv_results = {
        "Naive Bayes": nb_score,
        "Logistic Regression": lr_score,
        "Linear SVM": svm_score,
    }
    tuned_models = {
        "Naive Bayes": nb_model,
        "Logistic Regression": lr_model,
        "Linear SVM": svm_model,
    }

    ranked = sorted(cv_results.items(), key=lambda kv: kv[1], reverse=True)
    best_two_names = [ranked[0][0], ranked[1][0]]
    print(f"\nTop 2 TUNED models selected for voting ensemble: {best_two_names}")

    estimators = [(name, tuned_models[name]) for name in best_two_names]
    ensemble = VotingClassifier(estimators=estimators, voting="soft")

    print("\nTraining final voting ensemble (using tuned models) on training set...")
    ensemble.fit(X_train, y_train)

    preds = ensemble.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"\nHeld-out test accuracy (tuned voting ensemble): {acc:.2%}")
    print("\nClassification report:")
    print(classification_report(y_test, preds, target_names=["ham", "spam"]))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, preds))

    print("\nTop 20 spam-indicating features (from tuned Logistic Regression):")
    try:
        word_features = word_vectorizer.get_feature_names_out()
        char_features = char_vectorizer.get_feature_names_out()
        all_features = np.concatenate([word_features, char_features])
        coef = lr_model.coef_[0]
        top_idx = coef.argsort()[-20:][::-1]
        for i in top_idx:
            print(f"  {all_features[i]:20s}  weight={coef[i]:.4f}")
    except Exception as e:
        print(f"  (feature importance skipped: {e})")

    joblib.dump(ensemble, MODEL_PATH)
    joblib.dump(word_vectorizer, WORD_VECTORIZER_PATH)
    joblib.dump(char_vectorizer, CHAR_VECTORIZER_PATH)
    print(f"\nSaved model       -> {MODEL_PATH}")
    print(f"Saved word vectorizer -> {WORD_VECTORIZER_PATH}")
    print(f"Saved char vectorizer -> {CHAR_VECTORIZER_PATH}")
    print("\nDone. Start the API with: uvicorn main:app --reload --port 8000")


if __name__ == "__main__":
    main()
