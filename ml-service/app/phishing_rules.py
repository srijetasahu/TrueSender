"""
phishing_rules.py
-------------------
TrueSender - Rule-based phishing detection module (Member 3's piece).

This is intentionally rule-based (NOT machine learning) so it is a second,
independent detection technique alongside the ML classifier in train_model.py
/ main.py. Together they form the "hybrid" verdict.

8 checks performed:
 1. check_suspicious_urls()       - raw IP links, shortened URLs
 2. check_urgency_language()      - "act now", "within 24 hours", etc.
 3. check_sensitive_info()        - password, bank account, CVV, OTP, SSN
 4. check_generic_greeting()      - "Dear Customer", "Dear Winner", etc.
 5. check_sender_mismatch()       - display name vs actual domain mismatch
 6. check_excessive_punctuation() - more than 3 "!" or "?" in the email
 7. check_all_caps()              - 3+ ALL CAPS words
 8. check_attachment_mention()    - "see attached", "download file", etc.

risk_score = triggered_checks / 8
phishing_suspected = True if triggered_checks >= 2

Can be run directly for a quick manual test:
    python app/phishing_rules.py
"""

import re

# ---------------------------------------------------------------------------
# Keyword / phrase banks used by the checks below
# ---------------------------------------------------------------------------

URGENCY_PHRASES = [
    "act now", "act immediately", "urgent", "verify immediately",
    "within 24 hours", "final notice", "account suspended",
    "account will be closed", "limited time", "expires today",
    "click here now", "immediate action required", "last warning",
    "respond immediately", "your account will be locked",
]

SENSITIVE_INFO_PHRASES = [
    "password", "ssn", "social security", "bank account", "credit card",
    "otp", "one time password", "pin number", "cvv", "verify your identity",
    "confirm your details", "update your billing", "card number",
    "account number", "routing number",
]

GENERIC_GREETINGS = [
    "dear customer", "dear user", "dear valued customer", "dear member",
    "dear account holder", "dear winner", "dear sir/madam", "dear client",
]

SHORTENED_URL_DOMAINS = [
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly",
    "rebrand.ly", "cutt.ly",
]

ATTACHMENT_PHRASES = [
    "open attachment", "see attached", "download file", "open the attached",
    "please find attached", "download the file", "open this file",
    "view attachment",
]

KNOWN_BRANDS = [
    "paypal", "amazon", "microsoft", "apple", "google", "netflix", "bank",
    "facebook", "instagram", "linkedin", "chase", "wellsfargo",
]

URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)
IP_URL_PATTERN = re.compile(r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
WORD_PATTERN = re.compile(r"[A-Za-z]+")


def find_urls(text: str) -> list:
    return URL_PATTERN.findall(text)


# ---------------------------------------------------------------------------
# Check 1: Suspicious URLs
# ---------------------------------------------------------------------------
def check_suspicious_urls(text: str) -> dict:
    urls = find_urls(text)
    flags = []
    for url in urls:
        if IP_URL_PATTERN.match(url):
            flags.append(f"Raw IP address used as link: {url}")
        for short_domain in SHORTENED_URL_DOMAINS:
            if short_domain in url.lower():
                flags.append(f"Shortened/obscured URL detected: {url}")
    return {"triggered": len(flags) > 0, "details": flags, "url_count": len(urls)}


# ---------------------------------------------------------------------------
# Check 2: Urgency language
# ---------------------------------------------------------------------------
def check_urgency_language(text: str) -> dict:
    text_lower = text.lower()
    found = [p for p in URGENCY_PHRASES if p in text_lower]
    return {"triggered": len(found) > 0, "details": found}


# ---------------------------------------------------------------------------
# Check 3: Requests for sensitive information
# ---------------------------------------------------------------------------
def check_sensitive_info(text: str) -> dict:
    text_lower = text.lower()
    found = [p for p in SENSITIVE_INFO_PHRASES if p in text_lower]
    return {"triggered": len(found) > 0, "details": found}


# ---------------------------------------------------------------------------
# Check 4: Generic greeting
# ---------------------------------------------------------------------------
def check_generic_greeting(text: str) -> dict:
    text_lower = text.lower()
    found = [p for p in GENERIC_GREETINGS if p in text_lower]
    return {"triggered": len(found) > 0, "details": found}


# ---------------------------------------------------------------------------
# Check 5: Sender display-name vs domain mismatch
# ---------------------------------------------------------------------------
def check_sender_mismatch(display_name: str = "", sender_email: str = "") -> dict:
    if not display_name or not sender_email:
        return {"triggered": False, "details": []}

    display_lower = display_name.lower()
    domain = sender_email.split("@")[-1].lower() if "@" in sender_email else ""

    for brand in KNOWN_BRANDS:
        if brand in display_lower and brand not in domain:
            return {
                "triggered": True,
                "details": [f"Display name mentions '{brand}' but sender domain is '{domain}'"],
            }
    return {"triggered": False, "details": []}


# ---------------------------------------------------------------------------
# Check 6: Excessive punctuation
# ---------------------------------------------------------------------------
def check_excessive_punctuation(text: str) -> dict:
    exclamations = text.count("!")
    questions = text.count("?")
    total = exclamations + questions
    triggered = total > 3
    details = []
    if triggered:
        details.append(f"{exclamations} '!' and {questions} '?' found (threshold: 3)")
    return {"triggered": triggered, "details": details}


# ---------------------------------------------------------------------------
# Check 7: Excessive ALL CAPS words
# ---------------------------------------------------------------------------
def check_all_caps(text: str) -> dict:
    words = WORD_PATTERN.findall(text)
    # Only count words with 3+ letters so "A", "I", "OK" don't skew results
    caps_words = [w for w in words if len(w) >= 3 and w.isupper()]
    triggered = len(caps_words) >= 3
    return {"triggered": triggered, "details": caps_words[:10]}


# ---------------------------------------------------------------------------
# Check 8: Attachment mention
# ---------------------------------------------------------------------------
def check_attachment_mention(text: str) -> dict:
    text_lower = text.lower()
    found = [p for p in ATTACHMENT_PHRASES if p in text_lower]
    return {"triggered": len(found) > 0, "details": found}


# ---------------------------------------------------------------------------
# Master function: run all 8 checks and combine into one report
# ---------------------------------------------------------------------------
def analyze_phishing(email_text: str, display_name: str = "", sender_email: str = "") -> dict:
    """
    Runs all 8 heuristic checks and returns a combined phishing risk report.

    Returns:
        {
            "is_phishing_suspected": bool,
            "risk_score": float (0-1, fraction of checks triggered),
            "triggered_checks": int,
            "total_checks": int,
            "checks": { ... individual check results ... }
        }
    """
    checks = {
        "suspicious_urls": check_suspicious_urls(email_text),
        "urgency_language": check_urgency_language(email_text),
        "sensitive_info": check_sensitive_info(email_text),
        "generic_greeting": check_generic_greeting(email_text),
        "sender_mismatch": check_sender_mismatch(display_name, sender_email),
        "excessive_punctuation": check_excessive_punctuation(email_text),
        "all_caps": check_all_caps(email_text),
        "attachment_mention": check_attachment_mention(email_text),
    }

    triggered_count = sum(1 for c in checks.values() if c["triggered"])
    total_checks = len(checks)
    risk_score = triggered_count / total_checks
    is_phishing_suspected = triggered_count >= 2  # require 2+ signals to reduce false positives

    return {
        "is_phishing_suspected": is_phishing_suspected,
        "risk_score": round(risk_score, 2),
        "triggered_checks": triggered_count,
        "total_checks": total_checks,
        "checks": checks,
    }


if __name__ == "__main__":
    sample = (
        "Dear Customer, your PayPal account has been suspended. "
        "Verify your password and bank account IMMEDIATELY at http://192.168.5.2/verify "
        "or your account will be closed within 24 hours!!! Please see attached for details."
    )
    result = analyze_phishing(
        sample, display_name="PayPal Support", sender_email="support@paypa1-secure.ru"
    )
    print(f"Phishing suspected: {result['is_phishing_suspected']}")
    print(
        f"Risk score: {result['risk_score']} "
        f"({result['triggered_checks']}/{result['total_checks']} checks triggered)"
    )
    print("\nDetailed checks:")
    for name, check in result["checks"].items():
        status = "TRIGGERED" if check["triggered"] else "clear"
        print(f"  [{status}] {name}: {check['details']}")
