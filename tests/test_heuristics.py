from src.analyzer.heuristics import analyze


def test_clean_message_low_score() -> None:
    text = "Hello, are we still meeting at 3 today?"
    result = analyze(text)
    assert result.score < 30
    assert not result.suspicious_urls
    assert not result.requests_credentials


def test_credential_request_increases_score() -> None:
    text = "Send me your card number and CVV to receive your prize"
    result = analyze(text)
    assert result.requests_credentials
    assert result.has_lure
    assert result.score >= 50


def test_url_shortener_flagged() -> None:
    text = "Click here urgently to confirm your card: https://bit.ly/xyz"
    result = analyze(text)
    assert result.has_shortener
    assert result.has_urgency
    assert result.score > 0


def test_uzcard_lookalike_flagged() -> None:
    text = "Visit https://uzcard-bonus.com to claim your reward"
    result = analyze(text)
    assert any("uzcard" in u.registered_domain.lower() for u in result.suspicious_urls)


def test_userinfo_obfuscation_flagged() -> None:
    text = "Kartangiz bloklandi! Tasdiqlash: http://uzcard.uz@evil-scam.ru/verify"
    result = analyze(text)
    assert result.has_userinfo_trick
    assert any(u.registered_domain == "evil-scam.ru" for u in result.suspicious_urls)
    assert result.score >= 50
