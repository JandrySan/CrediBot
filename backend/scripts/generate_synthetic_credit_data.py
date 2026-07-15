from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import date
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.credit_bureau.synthetic_data import (  # noqa: E402
    SYNTHETIC_NAMESPACE,
    SyntheticCreditDataGenerator,
)

PEOPLE_COLUMNS = """
    id, national_id, phone_number, full_name, employment_status,
    reported_monthly_income, birth_date, gender, marital_status, province, city,
    address, occupation, employer_name, job_tenure_months, has_ruc,
    dependent_count, dataset_batch_id, is_synthetic, synthetic_key,
    economic_activity, business_tenure_months, other_monthly_income,
    monthly_living_expenses, housing_status, assets_total, liabilities_total,
    source_of_funds, identity_verified, income_verification_status, pep_status
"""
ACCOUNT_COLUMNS = """
    id, person_id, institution_name, product_type, original_amount,
    current_balance, monthly_payment, status, opened_at, closed_at,
    current_days_past_due, max_days_past_due, payment_rating, credit_limit,
    installment_frequency, collateral_type, restructured
"""
PAYMENT_COLUMNS = """
    account_id, period, due_amount, paid_amount, paid_at, days_late, payment_status
"""
SCORE_COLUMNS = "person_id, credit_score, risk_level, calculated_at"
INQUIRY_COLUMNS = """
    person_id, institution_name, inquiry_reason, channel, requested_amount, created_at
"""
RISK_COLUMNS = """
    person_id, event_type, severity, source_name, amount, status,
    occurred_at, resolved_at, notes
"""


def main() -> int:
    args = _parse_args()
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise SystemExit("DATABASE_URL no esta configurada.")
    if not database_url.startswith(("postgresql://", "postgres://")):
        raise SystemExit("El generador masivo requiere PostgreSQL.")

    batch_id = uuid.uuid5(SYNTHETIC_NAMESPACE, args.batch_key)
    generator = SyntheticCreditDataGenerator(
        batch_key=args.batch_key,
        batch_id=batch_id,
        seed=args.seed,
        reference_date=args.reference_date,
    )

    with psycopg2.connect(database_url) as connection:
        connection.autocommit = False
        with connection.cursor() as cursor:
            _assert_schema(cursor)
            if args.replace:
                cursor.execute(
                    "DELETE FROM credit_bureau.dataset_batches WHERE batch_key = %s",
                    (args.batch_key,),
                )
            cursor.execute(
                "SELECT status FROM credit_bureau.dataset_batches WHERE batch_key = %s",
                (args.batch_key,),
            )
            existing = cursor.fetchone()
            if existing:
                raise SystemExit(
                    f"El lote {args.batch_key} ya existe con estado {existing[0]}. "
                    "Usa --replace para regenerarlo."
                )

            cursor.execute(
                """
                INSERT INTO credit_bureau.dataset_batches (
                    id, batch_key, generator_version, random_seed, reference_date,
                    requested_people, status
                ) VALUES (%s, %s, %s, %s, %s, %s, 'LOADING')
                """,
                (
                    batch_id,
                    args.batch_key,
                    args.generator_version,
                    args.seed,
                    args.reference_date,
                    args.people,
                ),
            )

            totals = {
                "people": 0,
                "accounts": 0,
                "payments": 0,
                "scores": 0,
                "inquiries": 0,
                "risk_events": 0,
            }
            for start in range(1, args.people + 1, args.chunk_size):
                count = min(args.chunk_size, args.people - start + 1)
                chunk = generator.generate_chunk(start, count)
                _insert_chunk(cursor, chunk, args.page_size)
                for key, value in chunk.counts.items():
                    totals[key] += value
                print(
                    json.dumps(
                        {
                            "estado": "generando",
                            "personas_generadas": totals["people"],
                            "personas_solicitadas": args.people,
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )

            validation = _validate(cursor, batch_id, args.people)
            if not validation["valid"]:
                raise RuntimeError(f"La validacion del lote fallo: {validation}")

            cursor.execute(
                """
                UPDATE credit_bureau.dataset_batches SET
                    generated_people = %s,
                    generated_accounts = %s,
                    generated_payments = %s,
                    generated_scores = %s,
                    generated_inquiries = %s,
                    generated_risk_events = %s,
                    status = 'COMPLETED',
                    validation_summary = %s::jsonb,
                    completed_at = NOW()
                WHERE id = %s
                """,
                (
                    totals["people"],
                    totals["accounts"],
                    totals["payments"],
                    totals["scores"],
                    totals["inquiries"],
                    totals["risk_events"],
                    json.dumps(validation),
                    batch_id,
                ),
            )
        connection.commit()

    print(
        json.dumps(
            {
                "estado": "completado",
                "batch_key": args.batch_key,
                "batch_id": str(batch_id),
                "totales": totals,
                "validacion": validation,
            },
            ensure_ascii=False,
        )
    )
    return 0


def _insert_chunk(cursor, chunk, page_size: int) -> None:
    _execute_rows(cursor, "credit_bureau.people", PEOPLE_COLUMNS, chunk.people, page_size)
    _execute_rows(
        cursor, "credit_bureau.credit_accounts", ACCOUNT_COLUMNS, chunk.accounts, page_size
    )
    _execute_rows(
        cursor, "credit_bureau.payment_history", PAYMENT_COLUMNS, chunk.payments, page_size
    )
    _execute_rows(
        cursor, "credit_bureau.credit_score_snapshots", SCORE_COLUMNS, chunk.scores, page_size
    )
    _execute_rows(
        cursor, "credit_bureau.credit_inquiries", INQUIRY_COLUMNS, chunk.inquiries, page_size
    )
    _execute_rows(cursor, "credit_bureau.risk_events", RISK_COLUMNS, chunk.risk_events, page_size)


def _execute_rows(cursor, table: str, columns: str, rows: list[tuple], page_size: int) -> None:
    if not rows:
        return
    execute_values(
        cursor,
        f"INSERT INTO {table} ({columns}) VALUES %s",
        rows,
        page_size=page_size,
    )


def _assert_schema(cursor) -> None:
    cursor.execute(
        """
        SELECT
            to_regclass('credit_bureau.dataset_batches'),
            to_regclass('credit_bureau.people'),
            to_regclass('credit_bureau.credit_accounts'),
            to_regclass('credit_bureau.payment_history')
        """
    )
    if any(value is None for value in cursor.fetchone()):
        raise SystemExit("Faltan migraciones de credit_bureau; ejecuta Alembic antes de cargar.")


def _validate(cursor, batch_id: uuid.UUID, requested_people: int) -> dict:
    cursor.execute(
        """
        WITH batch_people AS (
            SELECT id, national_id, phone_number
            FROM credit_bureau.people
            WHERE dataset_batch_id = %s AND is_synthetic IS TRUE
        )
        SELECT
            COUNT(*) AS people,
            COUNT(*) FILTER (WHERE national_id !~ '^99[0-9]{8}$') AS invalid_ids,
            COUNT(*) FILTER (WHERE phone_number !~ '^\\+59398[0-9]{7}$') AS invalid_phones,
            COUNT(DISTINCT national_id) AS unique_ids,
            COUNT(DISTINCT phone_number) AS unique_phones
        FROM batch_people
        """,
        (batch_id,),
    )
    people, invalid_ids, invalid_phones, unique_ids, unique_phones = cursor.fetchone()
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM credit_bureau.credit_accounts account
        LEFT JOIN credit_bureau.people person ON person.id = account.person_id
        WHERE person.id IS NULL
        """
    )
    orphan_accounts = cursor.fetchone()[0]
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM credit_bureau.payment_history payment
        LEFT JOIN credit_bureau.credit_accounts account ON account.id = payment.account_id
        WHERE account.id IS NULL
        """
    )
    orphan_payments = cursor.fetchone()[0]
    valid = all(
        (
            people == requested_people,
            invalid_ids == 0,
            invalid_phones == 0,
            unique_ids == requested_people,
            unique_phones == requested_people,
            orphan_accounts == 0,
            orphan_payments == 0,
        )
    )
    return {
        "valid": valid,
        "people": people,
        "invalid_ids": invalid_ids,
        "invalid_phones": invalid_phones,
        "unique_ids": unique_ids,
        "unique_phones": unique_phones,
        "orphan_accounts": orphan_accounts,
        "orphan_payments": orphan_payments,
    }


def _parse_args():
    parser = argparse.ArgumentParser(description="Genera una central de riesgo sintetica.")
    parser.add_argument("--people", type=int, default=25000)
    parser.add_argument("--seed", type=int, default=20260715)
    parser.add_argument("--reference-date", type=date.fromisoformat, default=date(2026, 7, 15))
    parser.add_argument("--batch-key", default="credit-bureau-demo-2026-01")
    parser.add_argument("--generator-version", default="1.0.0")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--page-size", type=int, default=2000)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    if args.people <= 0 or args.people > 99999999:
        parser.error("--people debe estar entre 1 y 99999999")
    if args.chunk_size <= 0 or args.page_size <= 0:
        parser.error("--chunk-size y --page-size deben ser positivos")
    return args


if __name__ == "__main__":
    raise SystemExit(main())
