from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import ClassVar

SYNTHETIC_NAMESPACE = uuid.UUID("02b469e3-910f-4e73-9dc4-3d3b348c67c5")
MONEY = Decimal("0.01")


@dataclass
class SyntheticChunk:
    people: list[tuple]
    accounts: list[tuple]
    payments: list[tuple]
    scores: list[tuple]
    inquiries: list[tuple]
    risk_events: list[tuple]

    @property
    def counts(self) -> dict[str, int]:
        return {
            "people": len(self.people),
            "accounts": len(self.accounts),
            "payments": len(self.payments),
            "scores": len(self.scores),
            "inquiries": len(self.inquiries),
            "risk_events": len(self.risk_events),
        }


class SyntheticCreditDataGenerator:
    """Genera perfiles ficticios correlacionados sin usar datos de personas reales."""

    FIRST_NAMES = (
        "Ariana",
        "Bruno",
        "Camila",
        "Daniel",
        "Elena",
        "Fabian",
        "Gabriela",
        "Hector",
        "Ines",
        "Javier",
        "Karen",
        "Leonardo",
        "Monica",
        "Nicolas",
        "Olivia",
        "Patricio",
        "Renata",
        "Sebastian",
        "Tatiana",
        "Vicente",
    )
    LAST_NAMES = (
        "Alvarez",
        "Benitez",
        "Cabrera",
        "Dominguez",
        "Espinoza",
        "Flores",
        "Galarza",
        "Hidalgo",
        "Ibarra",
        "Jaramillo",
        "Lema",
        "Mendoza",
        "Navarrete",
        "Ortega",
        "Paredes",
        "Quintero",
        "Rivas",
        "Salazar",
        "Torres",
        "Vera",
    )
    LOCATIONS = (
        ("Guayas", "Guayaquil"),
        ("Pichincha", "Quito"),
        ("Manabi", "Manta"),
        ("Azuay", "Cuenca"),
        ("El Oro", "Machala"),
        ("Tungurahua", "Ambato"),
        ("Los Rios", "Quevedo"),
        ("Santo Domingo", "Santo Domingo"),
        ("Esmeraldas", "Esmeraldas"),
        ("Loja", "Loja"),
    )
    INSTITUTIONS = (
        "Banco Sintetico Andino",
        "Cooperativa Sintetica Costa",
        "Banco Demo Pacifico",
        "Financiera Laboratorio",
        "Almacen Credito Ficticio",
    )
    PRODUCT_CONFIG: ClassVar[dict[str, tuple[Decimal, Decimal, int]]] = {
        "PERSONAL_LOAN": (Decimal("600"), Decimal("25000"), 36),
        "CREDIT_CARD": (Decimal("500"), Decimal("12000"), 24),
        "VEHICLE_LOAN": (Decimal("7000"), Decimal("45000"), 60),
        "MORTGAGE": (Decimal("25000"), Decimal("150000"), 180),
        "MICROCREDIT": (Decimal("500"), Decimal("18000"), 30),
        "STORE_CREDIT": (Decimal("150"), Decimal("5000"), 18),
    }

    def __init__(
        self,
        batch_key: str,
        batch_id: uuid.UUID,
        seed: int,
        reference_date: date,
    ):
        self.batch_key = batch_key
        self.batch_id = batch_id
        self.seed = seed
        self.reference_date = reference_date

    def generate_chunk(self, start_index: int, count: int) -> SyntheticChunk:
        chunk = SyntheticChunk([], [], [], [], [], [])
        for index in range(start_index, start_index + count):
            self._generate_person(index, chunk)
        return chunk

    def _generate_person(self, index: int, chunk: SyntheticChunk) -> None:
        rng = random.Random(f"{self.seed}:person:{index}")
        person_id = self._uuid(f"person:{index}")
        tier = self._weighted(rng, (("LOW", 55), ("MEDIUM", 30), ("HIGH", 15)))
        employment = self._weighted(
            rng,
            (
                ("EMPLOYED", 56),
                ("SELF_EMPLOYED", 24),
                ("RETIRED", 9),
                ("UNEMPLOYED", 7),
                ("STUDENT", 4),
            ),
        )
        age = self._age_for_employment(rng, employment)
        birth_date = self.reference_date - timedelta(
            days=round(age * 365.2425 + rng.randint(0, 364))
        )
        income = self._income(rng, employment)
        other_income = self._money(income * Decimal(str(rng.uniform(0, 0.18))))
        expenses_ratio = Decimal(str(rng.uniform(0.32, 0.68)))
        expenses = self._money((income + other_income) * expenses_ratio)
        job_tenure = self._tenure(rng, employment, age)
        business_tenure = job_tenure if employment == "SELF_EMPLOYED" else 0
        province, city = rng.choice(self.LOCATIONS)
        first_name = rng.choice(self.FIRST_NAMES)
        first_last_name = rng.choice(self.LAST_NAMES)
        second_last_name = rng.choice(self.LAST_NAMES)
        full_name = f"{first_name} {first_last_name} {second_last_name} Demo {index:08d}"
        assets = self._money(max(income, Decimal("300")) * Decimal(str(rng.uniform(4, 50))))
        liabilities = self._money(assets * Decimal(str(rng.uniform(0.05, 0.75))))
        identity_verified = rng.random() < 0.97
        income_status = self._weighted(
            rng,
            (("VERIFIED", 70), ("DOCUMENTED", 20), ("DECLARED", 10)),
        )
        pep_status = self._weighted(rng, (("NOT_PEP", 97), ("UNKNOWN", 2), ("PEP", 1)))
        national_id = f"99{index:08d}"
        phone = f"+59398{index:07d}"
        synthetic_key = f"{self.batch_key}:person:{index}"

        chunk.people.append(
            (
                person_id,
                national_id,
                phone,
                full_name,
                employment,
                income,
                birth_date,
                rng.choice(("FEMALE", "MALE", "OTHER")),
                rng.choice(("SINGLE", "MARRIED", "DIVORCED", "WIDOWED")),
                province,
                city,
                f"Direccion sintetica {index:08d}",
                self._occupation(employment),
                self._employer(employment, index),
                job_tenure,
                employment == "SELF_EMPLOYED",
                rng.randint(0, 4),
                self.batch_id,
                True,
                synthetic_key,
                self._economic_activity(rng, employment),
                business_tenure,
                other_income,
                expenses,
                rng.choice(("OWN", "RENT", "FAMILY", "MORTGAGED")),
                assets,
                liabilities,
                self._source_of_funds(employment),
                identity_verified,
                income_status,
                pep_status,
            )
        )

        account_count = self._account_count(rng, tier)
        profile_max_dpd = 0
        for account_index in range(account_count):
            max_dpd = self._generate_account(
                rng,
                person_id,
                index,
                account_index,
                tier,
                income,
                chunk,
            )
            profile_max_dpd = max(profile_max_dpd, max_dpd)

        score = self._score(rng, tier, profile_max_dpd, account_count)
        chunk.scores.append(
            (
                person_id,
                score,
                "LOW" if score >= 700 else "MEDIUM" if score >= 580 else "HIGH",
                datetime.combine(self.reference_date, datetime.min.time(), tzinfo=UTC),
            )
        )
        self._generate_inquiries(rng, person_id, tier, income, chunk)
        self._generate_risk_events(rng, person_id, tier, index, chunk)

    def _generate_account(
        self,
        rng: random.Random,
        person_id: uuid.UUID,
        person_index: int,
        account_index: int,
        tier: str,
        income: Decimal,
        chunk: SyntheticChunk,
    ) -> int:
        account_id = self._uuid(f"person:{person_index}:account:{account_index}")
        product_type = self._weighted(
            rng,
            (
                ("PERSONAL_LOAN", 30),
                ("CREDIT_CARD", 26),
                ("VEHICLE_LOAN", 10),
                ("MORTGAGE", 6),
                ("MICROCREDIT", 18),
                ("STORE_CREDIT", 10),
            ),
        )
        minimum, maximum, typical_term = self.PRODUCT_CONFIG[product_type]
        affordability_cap = max(income * Decimal("18"), minimum)
        original = self._money(
            Decimal(str(rng.uniform(float(minimum), float(min(maximum, affordability_cap)))))
        )
        opened_months_ago = rng.randint(2, min(120, typical_term * 2))
        opened_at = self._month_start(opened_months_ago).replace(day=min(28, account_index + 1))
        term = max(6, round(typical_term * rng.uniform(0.65, 1.35)))
        elapsed_ratio = min(Decimal("1"), Decimal(opened_months_ago) / Decimal(term))
        scheduled_balance = original * (Decimal("1") - elapsed_ratio)
        monthly_payment = self._money(original / Decimal(term) * Decimal("1.18"))
        payment_months = min(opened_months_ago, rng.randint(8, 36))
        payment_rows: list[tuple] = []
        max_days_past_due = 0
        missed_count = 0
        for offset in range(payment_months, 0, -1):
            period = self._month_start(offset)
            payment_status = self._payment_status(rng, tier)
            days_late = self._days_late(rng, payment_status)
            max_days_past_due = max(max_days_past_due, days_late)
            missed_count += payment_status == "MISSED"
            paid_amount = {
                "ON_TIME": monthly_payment,
                "LATE": monthly_payment,
                "PARTIAL": self._money(monthly_payment * Decimal(str(rng.uniform(0.25, 0.8)))),
                "MISSED": Decimal("0.00"),
            }[payment_status]
            paid_at = None if payment_status == "MISSED" else period + timedelta(days=days_late)
            payment_rows.append(
                (
                    account_id,
                    period,
                    monthly_payment,
                    paid_amount,
                    paid_at,
                    days_late,
                    payment_status,
                )
            )

        is_currently_bad = tier == "HIGH" and (missed_count > 0 or max_days_past_due > 30)
        if is_currently_bad and rng.random() < 0.7:
            status = "OVERDUE" if rng.random() < 0.82 else "WRITTEN_OFF"
            current_dpd = max(31, max_days_past_due)
            balance = max(scheduled_balance, original * Decimal("0.2"))
        elif opened_months_ago >= term:
            status = "CLOSED"
            current_dpd = 0
            balance = Decimal("0")
        else:
            status = "ACTIVE"
            current_dpd = 0
            balance = scheduled_balance

        max_days_past_due = max(max_days_past_due, current_dpd)
        rating = self._rating(max_days_past_due, status)
        credit_limit = original if product_type == "CREDIT_CARD" else Decimal("0")
        chunk.accounts.append(
            (
                account_id,
                person_id,
                rng.choice(self.INSTITUTIONS),
                product_type,
                original,
                self._money(balance),
                monthly_payment if status != "CLOSED" else Decimal("0.00"),
                status,
                opened_at,
                self.reference_date if status == "CLOSED" else None,
                current_dpd,
                max_days_past_due,
                rating,
                credit_limit,
                "MONTHLY",
                "MORTGAGE" if product_type == "MORTGAGE" else None,
                tier == "HIGH" and rng.random() < 0.15,
            )
        )
        chunk.payments.extend(payment_rows)
        return max_days_past_due

    def _generate_inquiries(self, rng, person_id, tier, income, chunk) -> None:
        maximum = {"LOW": 3, "MEDIUM": 6, "HIGH": 10}[tier]
        for inquiry_index in range(rng.randint(0, maximum)):
            created_at = datetime.combine(
                self.reference_date - timedelta(days=rng.randint(1, 365)),
                datetime.min.time(),
                tzinfo=UTC,
            ) + timedelta(minutes=inquiry_index)
            chunk.inquiries.append(
                (
                    person_id,
                    rng.choice(self.INSTITUTIONS),
                    "CREDIT_APPLICATION",
                    rng.choice(("DIGITAL", "BRANCH", "WHATSAPP")),
                    self._money(income * Decimal(str(rng.uniform(1, 10)))),
                    created_at,
                )
            )

    def _generate_risk_events(self, rng, person_id, tier, person_index, chunk) -> None:
        probability = {"LOW": 0.01, "MEDIUM": 0.08, "HIGH": 0.38}[tier]
        if rng.random() >= probability:
            return
        event_type = rng.choice(
            (
                "JUDICIAL_COLLECTION",
                "WRITTEN_OFF",
                "RESTRUCTURED",
                "REFINANCED",
                "FRAUD_ALERT",
                "RETURNED_CHECK",
            )
        )
        occurred_at = self.reference_date - timedelta(days=rng.randint(30, 1500))
        resolved = tier != "HIGH" and rng.random() < 0.65
        chunk.risk_events.append(
            (
                person_id,
                event_type,
                "HIGH" if tier == "HIGH" else "MEDIUM",
                "Fuente sintetica controlada",
                self._money(Decimal(str(rng.uniform(100, 8000)))),
                "RESOLVED" if resolved else "ACTIVE",
                occurred_at,
                occurred_at + timedelta(days=rng.randint(30, 300)) if resolved else None,
                f"Evento completamente sintetico del perfil {person_index:08d}",
            )
        )

    def _uuid(self, key: str) -> uuid.UUID:
        return uuid.uuid5(SYNTHETIC_NAMESPACE, f"{self.batch_key}:{key}")

    @staticmethod
    def _weighted(rng: random.Random, choices: tuple[tuple[str, int], ...]) -> str:
        values, weights = zip(*choices, strict=True)
        return rng.choices(values, weights=weights, k=1)[0]

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return max(value, Decimal("0")).quantize(MONEY, rounding=ROUND_HALF_UP)

    def _month_start(self, months_ago: int) -> date:
        total_months = self.reference_date.year * 12 + self.reference_date.month - 1 - months_ago
        return date(total_months // 12, total_months % 12 + 1, 1)

    @staticmethod
    def _age_for_employment(rng, employment) -> int:
        ranges = {
            "EMPLOYED": (21, 64),
            "SELF_EMPLOYED": (23, 68),
            "RETIRED": (60, 74),
            "UNEMPLOYED": (21, 64),
            "STUDENT": (18, 30),
        }
        return rng.randint(*ranges[employment])

    @staticmethod
    def _income(rng, employment) -> Decimal:
        ranges = {
            "EMPLOYED": (550, 4500),
            "SELF_EMPLOYED": (450, 6500),
            "RETIRED": (450, 2600),
            "UNEMPLOYED": (0, 500),
            "STUDENT": (0, 700),
        }
        minimum, maximum = ranges[employment]
        return Decimal(str(round(rng.triangular(minimum, maximum, minimum * 1.8), 2)))

    @staticmethod
    def _tenure(rng, employment, age) -> int:
        if employment not in {"EMPLOYED", "SELF_EMPLOYED"}:
            return 0
        return rng.randint(1, max(2, min((age - 18) * 12, 240)))

    @staticmethod
    def _occupation(employment: str) -> str:
        return {
            "EMPLOYED": "Profesional dependiente sintetico",
            "SELF_EMPLOYED": "Comerciante independiente sintetico",
            "RETIRED": "Jubilado sintetico",
            "UNEMPLOYED": "Sin empleo formal",
            "STUDENT": "Estudiante sintetico",
        }[employment]

    @staticmethod
    def _employer(employment: str, index: int) -> str:
        if employment == "SELF_EMPLOYED":
            return f"Negocio sintetico {index:08d}"
        if employment == "EMPLOYED":
            return f"Empresa sintetica {index % 250:03d}"
        return "No aplica"

    @staticmethod
    def _economic_activity(rng, employment) -> str:
        if employment == "SELF_EMPLOYED":
            return rng.choice(("COMERCIO", "SERVICIOS", "AGRICULTURA", "TRANSPORTE"))
        return "RELACION_DE_DEPENDENCIA" if employment == "EMPLOYED" else "NO_APLICA"

    @staticmethod
    def _source_of_funds(employment: str) -> str:
        return {
            "EMPLOYED": "SUELDO",
            "SELF_EMPLOYED": "VENTAS_DEL_NEGOCIO",
            "RETIRED": "PENSION",
            "UNEMPLOYED": "APOYO_FAMILIAR",
            "STUDENT": "APOYO_FAMILIAR",
        }[employment]

    @staticmethod
    def _account_count(rng, tier) -> int:
        choices = {
            "LOW": ((0, 8), (1, 30), (2, 35), (3, 20), (4, 7)),
            "MEDIUM": ((0, 5), (1, 20), (2, 30), (3, 27), (4, 13), (5, 5)),
            "HIGH": ((0, 4), (1, 15), (2, 24), (3, 27), (4, 18), (5, 12)),
        }[tier]
        values, weights = zip(*choices, strict=True)
        return rng.choices(values, weights=weights, k=1)[0]

    @staticmethod
    def _payment_status(rng, tier) -> str:
        choices = {
            "LOW": (("ON_TIME", 94), ("LATE", 5), ("PARTIAL", 1), ("MISSED", 0)),
            "MEDIUM": (("ON_TIME", 78), ("LATE", 15), ("PARTIAL", 5), ("MISSED", 2)),
            "HIGH": (("ON_TIME", 50), ("LATE", 23), ("PARTIAL", 12), ("MISSED", 15)),
        }[tier]
        values, weights = zip(*choices, strict=True)
        return rng.choices(values, weights=weights, k=1)[0]

    @staticmethod
    def _days_late(rng, payment_status) -> int:
        if payment_status == "ON_TIME":
            return 0
        if payment_status == "LATE":
            return rng.randint(1, 30)
        if payment_status == "PARTIAL":
            return rng.randint(15, 60)
        return rng.choice((30, 60, 90, 120, 180))

    @staticmethod
    def _rating(max_dpd: int, status: str) -> str:
        if status == "WRITTEN_OFF" or max_dpd > 120:
            return "E"
        if max_dpd > 60:
            return "D"
        if max_dpd > 30:
            return "C"
        if max_dpd > 0:
            return "B"
        return "A"

    @staticmethod
    def _score(rng, tier, max_dpd, account_count) -> int:
        ranges = {"LOW": (690, 825), "MEDIUM": (570, 699), "HIGH": (350, 579)}
        minimum, maximum = ranges[tier]
        score = rng.randint(minimum, maximum) - min(100, max_dpd // 2)
        if account_count == 0:
            score = min(score, 650)
        return max(300, min(850, score))
