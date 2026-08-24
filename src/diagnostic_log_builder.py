"""Create a sanitized Markdown diagnostic log without contacting external services."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
IPV4_PATTERN = re.compile(r"\b(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}\b")
URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)
WINDOWS_USER_PATH = re.compile(r"(?i)C:\\Users\\[^\\\s]+")
TOKEN_PATTERN = re.compile(
    r"(?i)\b(?:ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+)\b"
)
KEY_VALUE_SECRET = re.compile(
    r"(?i)\b(?:authorization|api[_-]?key|token|secret)\s*[:=]\s*\S+"
)


def redact_sensitive_text(value: str) -> str:
    """Replace common support-note identifiers with clear markers."""

    redacted = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", value)
    redacted = IPV4_PATTERN.sub("[REDACTED_IP]", redacted)
    redacted = URL_PATTERN.sub("[REDACTED_URL]", redacted)
    redacted = WINDOWS_USER_PATH.sub(lambda _: r"C:\Users\[REDACTED_USER]", redacted)
    redacted = TOKEN_PATTERN.sub("[REDACTED_TOKEN]", redacted)
    return KEY_VALUE_SECRET.sub("[REDACTED_SECRET]", redacted)


def count_markers(value: str) -> int:
    return value.count("[REDACTED_")


def build_log(ticket_id: str, device: str, symptom: str) -> str:
    safe_ticket_id = redact_sensitive_text(ticket_id).strip() or "UNASSIGNED"
    safe_device = redact_sensitive_text(device).strip() or "UNASSIGNED"
    safe_symptom = redact_sensitive_text(symptom).strip() or "No symptom supplied."

    return "\n".join(
        [
            "# Sanitized Diagnostic Log",
            "",
            "## Context",
            "",
            f"- Ticket ID: {safe_ticket_id}",
            f"- Device: {safe_device}",
            "- External services contacted: none",
            "",
            "## Reported Symptom",
            "",
            "~~~text",
            safe_symptom,
            "~~~",
            "",
            "## First-Pass Workflow",
            "",
            "1. Confirm the exact symptom and recent change.",
            "2. Run read-only diagnostics before attempting a repair.",
            "3. Treat research output as hypotheses to verify.",
            "4. Check commands and settings against authoritative documentation.",
            "5. Record the result of one reversible action at a time.",
            "",
            "## Verification Record",
            "",
            "| Hypothesis | Evidence | Read-only check | Result | Next decision |",
            "| --- | --- | --- | --- | --- |",
            "|  |  |  |  |  |",
            "",
            "## Review Note",
            "",
            "This output uses pattern-based redaction. A technician must review it before sharing it outside the approved support environment.",
            "",
        ]
    )


def write_log(content: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a sanitized diagnostic log from a local symptom note."
    )
    parser.add_argument("--ticket-id", required=True, help="Ticket identifier or sanitized label.")
    parser.add_argument("--device", required=True, help="Device name or sanitized label.")
    parser.add_argument("--symptom-file", required=True, type=Path, help="Text file containing the symptom.")
    parser.add_argument("--out", required=True, type=Path, help="Markdown output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        symptom = args.symptom_file.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Unable to read symptom file: {exc}")
        return 2

    log = build_log(args.ticket_id, args.device, symptom)
    write_log(log, args.out)
    print(f"Sanitized log written to {args.out.resolve()}")
    print(f"Redaction markers inserted: {count_markers(log)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
