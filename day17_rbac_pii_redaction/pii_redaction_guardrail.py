"""Presidio-backed PII redaction for text sent to an LLM."""

from functools import lru_cache

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

ENTITIES = (
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "PATIENT_ID",
)


@lru_cache(maxsize=1)
def _engines() -> tuple[AnalyzerEngine, AnonymizerEngine]:
    analyzer = AnalyzerEngine()
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="PATIENT_ID",
            name="PatientIdRecognizer",
            patterns=[
                Pattern(
                    name="patient_id",
                    regex=(
                        r"\b(?:MRN|patient(?:\s+(?:id|number))?)"
                        r"\s*[:#-]?\s*(?=[A-Z0-9-]*\d)[A-Z0-9][A-Z0-9-]{3,}\b"
                    ),
                    score=0.85,
                )
            ],
            context=["patient", "patient id", "patient number", "mrn"],
        )
    )
    return analyzer, AnonymizerEngine()


def scrub_enterprise_pii(raw_text: str) -> tuple[str, dict[str, int]]:
    """Replace supported PII with typed tokens and return per-entity counts."""
    analyzer, anonymizer = _engines()
    findings = analyzer.analyze(text=raw_text, language="en", entities=list(ENTITIES))
    redaction_counts: dict[str, int] = {}
    for finding in findings:
        redaction_counts[finding.entity_type] = (
            redaction_counts.get(finding.entity_type, 0) + 1
        )

    operators = {
        entity: OperatorConfig("replace", {"new_value": f"<{entity}>"})
        for entity in ENTITIES
    }
    result = anonymizer.anonymize(
        text=raw_text,
        analyzer_results=findings,
        operators=operators,
    )
    return result.text, redaction_counts


if __name__ == "__main__":
    dirty_ticket = (
        "Patient John Doe (MRN: MRN-123456, credit card 4111-1111-1111-1111, "
        "email john.doe@example.org, phone 415-890-2211) needs assistance."
    )
    clean_prompt, stats = scrub_enterprise_pii(dirty_ticket)
    print("Safe LLM Prompt (PII Scrubbed):\n", clean_prompt)
    print("Governance Audit Metrics:", stats)
