import re

class SecurityRedactor:
    """
    Sanitizes incoming prompts and document text before sending to LLM / vector indexing.
    Redacts PII (Emails, Phone numbers, IPs, Passwords, Serial keys).
    """
    
    PATTERNS = {
        "EMAIL": r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
        "PHONE": r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        "IP_ADDRESS": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        "PASSWORD_KEY": r'(?i)(?:password|secret|apikey|token|key)\s*[:=]\s*\S+',
        "EMPLOYEE_ID": r'\bEMP-\d{4,6}\b'
    }

    @classmethod
    def sanitize(cls, text: str) -> dict:
        redacted_text = text
        redaction_count = 0
        redact_details = []

        for category, pattern in cls.PATTERNS.items():
            matches = re.findall(pattern, redacted_text)
            if matches:
                redaction_count += len(matches)
                redact_details.append(f"Redacted {len(matches)} instance(s) of {category}")
                redacted_text = re.sub(pattern, f"[{category}_REDACTED]", redacted_text)

        return {
            "clean_text": redacted_text,
            "redacted": redaction_count > 0,
            "redaction_count": redaction_count,
            "details": redact_details
        }

security_redactor = SecurityRedactor()
