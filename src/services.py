import hashlib
import re
import streamlit as st
import anthropic
from src.scanner import scan_for_phi

# 1. Configure Anthropic Client
# We use the new key name we just added to your secrets.toml
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

_TONE_MAP = {
    "HIGH":   "URGENT — critical HIPAA violation requiring immediate escalation.",
    "MEDIUM": "SIGNIFICANT — prompt compliance review and containment required.",
    "LOW":    "MINIMAL — standard monitoring protocols apply.",
}

def _strip_markdown(text: str) -> str:
    """Remove Markdown formatting that the AI sometimes emits despite instructions."""
    # Drop leading # headers on any line (e.g. "# EXECUTIVE RISK BRIEF")
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    # Unwrap bold/italic markers (**text**, *text*, __text__, _text_)
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"_{1,3}(.*?)_{1,3}",   r"\1", text, flags=re.DOTALL)
    return text.strip()

def get_risk_summary(scan_results, phi_count: int, risk_level: str):
    """Generates a HIPAA-compliant risk summary using Anthropic Claude."""
    phones = scan_results.get("phones", [])
    emails = scan_results.get("emails", [])

    phi_details = []
    if phones:
        sample = ", ".join(phones[:3])
        more   = f" (+{len(phones) - 3} more)" if len(phones) > 3 else ""
        phi_details.append(f"{len(phones)} phone number(s) — e.g. {sample}{more}")
    if emails:
        sample = ", ".join(emails[:3])
        more   = f" (+{len(emails) - 3} more)" if len(emails) > 3 else ""
        phi_details.append(f"{len(emails)} email address(es) — e.g. {sample}{more}")

    phi_description = "; ".join(phi_details) if phi_details else "unspecified PHI elements"
    tone_guidance   = _TONE_MAP.get(risk_level, _TONE_MAP["MEDIUM"])

    prompt = (
        "You are a senior HIPAA compliance officer writing a formal executive risk brief. "
        f"This file has {phi_count} PHI/PII finding(s) and is classified as {risk_level} RISK. "
        f"Detected data: {phi_description}. "
        f"Tone directive: {tone_guidance} "
        "Write exactly two sentences: "
        "(1) Name the specific data types exposed and state the severity of the compliance risk they represent. "
        "(2) State the required remediation action, scaled to the risk level. "
        "FORMATTING RULES: Do not use Markdown headers (#), bold (**), italic (*), or any other "
        "Markdown syntax. Plain prose only. No preamble. No hedging. Formal, authoritative."
    )

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return _strip_markdown(message.content[0].text)
    except Exception as e:
        return f"Summary unavailable: {str(e)}"

def process_compliance_scan(content: str):
    """
    Service layer to wrap the scanning logic, add enterprise features,
    and generate AI risk summaries.
    """
    # 1. Get the results from your existing scanner
    scan_results = scan_for_phi(content)

    # 2. Generate the SHA-256 Hash
    file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

    # 3. Perform the sanitization
    sanitized_text = content
    for p in scan_results.get("phones", []):
        sanitized_text = sanitized_text.replace(p, "[PHONE_REDACTED]")
    for e in scan_results.get("emails", []):
        sanitized_text = sanitized_text.replace(e, "[EMAIL_REDACTED]")

    # 4. Three-tier risk level: HIGH ≥ 4 findings, MEDIUM 1-3, LOW 0
    phi_count  = len(scan_results.get("phones", [])) + len(scan_results.get("emails", []))
    risk_level = "HIGH" if phi_count >= 4 else ("MEDIUM" if phi_count >= 1 else "LOW")

    # 5. Generate AI Risk Summary for HIGH and MEDIUM findings
    risk_summary = None
    if phi_count > 0:
        risk_summary = get_risk_summary(scan_results, phi_count, risk_level)

    # 6. Return the combined dictionary
    return {
        **scan_results,
        "hash":           file_hash,
        "sanitized_text": sanitized_text,
        "risk_summary":   risk_summary,
        "risk_level":     risk_level,
    }