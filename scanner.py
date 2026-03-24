import re

FILE_PATH = "test_data.txt"

PHONE_PATTERN = re.compile(
    r'(\+1\s?)?(\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4})'
)
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
)

def scan_file(path):
    with open(path, "r") as f:
        content = f.read()

    phones = PHONE_PATTERN.findall(content)
    emails = EMAIL_PATTERN.findall(content)

    print(f"=== Scanning: {path} ===\n")

    print("Phone numbers found:")
    if phones:
        for prefix, number in phones:
            full = (prefix + number).strip()
            print(f"  {full}")
    else:
        print("  None found.")

    print("\nEmails found:")
    if emails:
        for email in emails:
            print(f"  {email}")
    else:
        print("  None found.")

def scan_for_phi(content: str) -> dict:
    phones = PHONE_PATTERN.findall(content)
    emails = EMAIL_PATTERN.findall(content)

    phone_list = [(prefix + number).strip() for prefix, number in phones]
    email_list = list(emails)

    sanitized = content
    for item in phone_list:
        print(f"REDACTING: {item} -> [REDACTED]")
        sanitized = sanitized.replace(item, "[REDACTED]")
    for item in email_list:
        print(f"REDACTING: {item} -> [REDACTED]")
        sanitized = sanitized.replace(item, "[REDACTED]")

    return {
        "phones": phone_list,
        "emails": email_list,
        "phi_found": bool(phone_list or email_list),
        "sanitized_text": sanitized,
    }

if __name__ == "__main__":
    scan_file(FILE_PATH)
