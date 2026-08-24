import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from diagnostic_log_builder import build_log, count_markers, redact_sensitive_text


class DiagnosticLogBuilderTests(unittest.TestCase):
    def test_redacts_common_sensitive_values(self) -> None:
        source = (
            "sample.user@example.invalid at http://10.20.30.40:8080 "
            r"from C:\Users\SampleUser\Desktop, host 10.20.30.40, token=sample-token"
        )

        redacted = redact_sensitive_text(source)

        self.assertNotIn("sample.user@example.invalid", redacted)
        self.assertNotIn("10.20.30.40", redacted)
        self.assertNotIn("SampleUser", redacted)
        self.assertIn("[REDACTED_EMAIL]", redacted)
        self.assertIn("[REDACTED_URL]", redacted)
        self.assertIn("[REDACTED_USER]", redacted)
        self.assertIn("[REDACTED_SECRET]", redacted)

    def test_build_log_marks_external_services_as_none(self) -> None:
        log = build_log("LAB-001", "LAB-DEVICE", "Synthetic symptom")

        self.assertIn("External services contacted: none", log)
        self.assertIn("Synthetic symptom", log)

    def test_marker_count_tracks_redactions(self) -> None:
        self.assertEqual(count_markers("[REDACTED_EMAIL] [REDACTED_IP]"), 2)


if __name__ == "__main__":
    unittest.main()
