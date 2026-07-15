import uuid
from datetime import date
from decimal import Decimal

from app.services.credit_bureau.synthetic_data import SyntheticCreditDataGenerator


def test_synthetic_generator_is_reproducible_and_relationally_consistent():
    batch_id = uuid.UUID("eff51351-317e-52fc-9720-5e51f9fa2175")
    generator = SyntheticCreditDataGenerator(
        batch_key="test-batch",
        batch_id=batch_id,
        seed=20260715,
        reference_date=date(2026, 7, 15),
    )

    first = generator.generate_chunk(1, 100)
    second = generator.generate_chunk(1, 100)

    assert first.people == second.people
    assert first.accounts == second.accounts
    assert first.payments == second.payments
    assert len(first.people) == 100
    assert len(first.scores) == 100

    person_ids = {row[0] for row in first.people}
    account_ids = {row[0] for row in first.accounts}
    assert all(row[1] in person_ids for row in first.accounts)
    assert all(row[0] in account_ids for row in first.payments)
    assert all(row[0] in person_ids for row in first.scores)
    assert all(row[0] in person_ids for row in first.inquiries)
    assert all(row[0] in person_ids for row in first.risk_events)


def test_synthetic_identifiers_are_reserved_and_financial_values_are_coherent():
    generator = SyntheticCreditDataGenerator(
        batch_key="test-batch-values",
        batch_id=uuid.UUID("adc568cb-4f92-52ca-82a2-2355462d186d"),
        seed=77,
        reference_date=date(2026, 7, 15),
    )
    chunk = generator.generate_chunk(1, 250)

    national_ids = [row[1] for row in chunk.people]
    phones = [row[2] for row in chunk.people]
    assert len(set(national_ids)) == 250
    assert len(set(phones)) == 250
    assert all(value.startswith("99") and len(value) == 10 for value in national_ids)
    assert all(value.startswith("+59398") and len(value) == 13 for value in phones)
    assert all(row[18] is True for row in chunk.people)
    assert all("Demo" in row[3] for row in chunk.people)

    assert all(row[4] >= Decimal("0") for row in chunk.accounts)
    assert all(row[5] >= Decimal("0") for row in chunk.accounts)
    assert all(row[6] >= Decimal("0") for row in chunk.accounts)
    assert all(300 <= row[1] <= 850 for row in chunk.scores)
