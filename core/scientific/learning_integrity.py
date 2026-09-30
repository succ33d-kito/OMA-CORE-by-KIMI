"""Fail-closed promotion quarantine until verified cross-store lineage exists.

Unvalidated research candidates can still be audited. They are not learned
knowledge and have no authority over Criterion or operational policy. A boolean
supplied by a caller is deliberately not an override for this quarantine.
"""


class LearningIntegrityError(ValueError):
    pass


def require_promotion_authority():
    raise LearningIntegrityError(
        'LEARNING_QUARANTINED: verified decision/hypothesis/evidence/outcome '
        'lineage and independent scientific gate receipts are not integrated; '
        'Knowledge validation and Criterion application are disabled'
    )


def quarantine_candidate(knowledge):
    knowledge.provenance = {
        **knowledge.provenance,
        'learning_eligible': False,
        'integrity_status': 'QUARANTINED_UNVALIDATED_RESEARCH_CANDIDATE',
    }
