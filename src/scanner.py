import re
import hashlib

# Define patterns
PHONE_PATTERN = re.compile(r'(\+1\s?)?(\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4})')
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

def get_file_hash(content: str) -> str:
    """Creates a unique SHA-256 fingerprint for the file content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def scan_for_phi(content: str) -> dict:
    """Scans, masks, and hashes content for enterprise-grade compliance."""
    try:
        # 1. Create Audit Fingerprint
        file_hash = get_file_hash(content)
        
        # 2. Extract matches
        phones = PHONE_PATTERN.findall(content)
        emails = EMAIL_PATTERN.findall(content)
        
        # Format the phone list for the report
        phone_list = [(prefix + number).strip() for prefix, number in phones]
        email_list = list(emails)
        
        # 3. Optimized Redaction using Regex substitution
        # We replace the actual matched text with the redaction tag
        sanitized = PHONE_PATTERN.sub("[PHONE_REDACTED]", content)
        sanitized = EMAIL_PATTERN.sub("[EMAIL_REDACTED]", sanitized)
        
        return {
            "hash": file_hash,
            "phones": phone_list,
            "emails": email_list,
            "phi_found": bool(phone_list or email_list),
            "sanitized_text": sanitized,
            "error": None
        }
        
    except Exception as e:
        return {
            "hash": None,
            "phones": [],
            "emails": [],
            "phi_found": False,
            "sanitized_text": None,
            "error": str(e)
        }