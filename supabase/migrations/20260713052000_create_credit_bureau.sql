-- CrediBot - Base simulada de historial crediticio
-- PostgreSQL / Supabase
-- Datos totalmente ficticios para uso academico.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS credit_bureau;

CREATE TABLE IF NOT EXISTS credit_bureau.people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    national_id VARCHAR(10) NOT NULL UNIQUE,
    phone_number VARCHAR(20) UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    employment_status VARCHAR(30) NOT NULL DEFAULT 'EMPLOYED'
        CHECK (
            employment_status IN (
                'EMPLOYED',
                'SELF_EMPLOYED',
                'UNEMPLOYED',
                'RETIRED',
                'STUDENT'
            )
        ),
    reported_monthly_income NUMERIC(12, 2) NOT NULL DEFAULT 0
        CHECK (reported_monthly_income >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_credit_people_national_id
ON credit_bureau.people(national_id);

CREATE INDEX IF NOT EXISTS idx_credit_people_phone
ON credit_bureau.people(phone_number);

CREATE TABLE IF NOT EXISTS credit_bureau.credit_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID NOT NULL
        REFERENCES credit_bureau.people(id)
        ON DELETE CASCADE,
    institution_name VARCHAR(120) NOT NULL,
    product_type VARCHAR(30) NOT NULL
        CHECK (
            product_type IN (
                'PERSONAL_LOAN',
                'CREDIT_CARD',
                'VEHICLE_LOAN',
                'MORTGAGE',
                'MICROCREDIT',
                'STORE_CREDIT'
            )
        ),
    original_amount NUMERIC(12, 2) NOT NULL
        CHECK (original_amount >= 0),
    current_balance NUMERIC(12, 2) NOT NULL DEFAULT 0
        CHECK (current_balance >= 0),
    monthly_payment NUMERIC(12, 2) NOT NULL DEFAULT 0
        CHECK (monthly_payment >= 0),
    status VARCHAR(20) NOT NULL
        CHECK (
            status IN (
                'ACTIVE',
                'CLOSED',
                'OVERDUE',
                'WRITTEN_OFF'
            )
        ),
    opened_at DATE NOT NULL,
    closed_at DATE,
    current_days_past_due INTEGER NOT NULL DEFAULT 0
        CHECK (current_days_past_due >= 0),
    max_days_past_due INTEGER NOT NULL DEFAULT 0
        CHECK (max_days_past_due >= 0),
    payment_rating VARCHAR(5) NOT NULL DEFAULT 'A'
        CHECK (payment_rating IN ('A', 'B', 'C', 'D', 'E')),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_credit_accounts_person
ON credit_bureau.credit_accounts(person_id);

CREATE INDEX IF NOT EXISTS idx_credit_accounts_status
ON credit_bureau.credit_accounts(status);

CREATE UNIQUE INDEX IF NOT EXISTS uq_credit_accounts_seed_identity
ON credit_bureau.credit_accounts(person_id, institution_name, product_type, opened_at);

CREATE TABLE IF NOT EXISTS credit_bureau.payment_history (
    id BIGSERIAL PRIMARY KEY,
    account_id UUID NOT NULL
        REFERENCES credit_bureau.credit_accounts(id)
        ON DELETE CASCADE,
    period DATE NOT NULL,
    due_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    paid_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    paid_at DATE,
    days_late INTEGER NOT NULL DEFAULT 0,
    payment_status VARCHAR(20) NOT NULL
        CHECK (
            payment_status IN (
                'ON_TIME',
                'LATE',
                'PARTIAL',
                'MISSED'
            )
        ),
    UNIQUE(account_id, period)
);

CREATE INDEX IF NOT EXISTS idx_payment_history_account
ON credit_bureau.payment_history(account_id);

CREATE TABLE IF NOT EXISTS credit_bureau.credit_score_snapshots (
    id BIGSERIAL PRIMARY KEY,
    person_id UUID NOT NULL
        REFERENCES credit_bureau.people(id)
        ON DELETE CASCADE,
    credit_score INTEGER NOT NULL
        CHECK (credit_score BETWEEN 300 AND 850),
    risk_level VARCHAR(10) NOT NULL
        CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_credit_score_person
ON credit_bureau.credit_score_snapshots(person_id, calculated_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_credit_score_seed_person_score
ON credit_bureau.credit_score_snapshots(person_id, credit_score, risk_level);

CREATE OR REPLACE VIEW credit_bureau.credit_profile_summary AS
WITH latest_score AS (
    SELECT DISTINCT ON (person_id)
        person_id,
        credit_score,
        risk_level,
        calculated_at
    FROM credit_bureau.credit_score_snapshots
    ORDER BY person_id, calculated_at DESC
),
account_summary AS (
    SELECT
        person_id,
        COUNT(*) AS total_accounts,
        COUNT(*) FILTER (WHERE status = 'ACTIVE') AS active_accounts,
        COUNT(*) FILTER (WHERE status IN ('OVERDUE', 'WRITTEN_OFF')) AS problematic_accounts,
        COALESCE(SUM(current_balance) FILTER (WHERE status IN ('ACTIVE', 'OVERDUE')), 0)
            AS total_outstanding_debt,
        COALESCE(SUM(monthly_payment) FILTER (WHERE status IN ('ACTIVE', 'OVERDUE')), 0)
            AS total_monthly_debt_payment,
        COALESCE(MAX(max_days_past_due), 0) AS max_days_past_due,
        COUNT(*) FILTER (WHERE current_days_past_due > 0) AS overdue_accounts
    FROM credit_bureau.credit_accounts
    GROUP BY person_id
),
payment_summary AS (
    SELECT
        ca.person_id,
        COUNT(*) FILTER (WHERE ph.payment_status = 'MISSED') AS missed_payments,
        COUNT(*) FILTER (WHERE ph.payment_status = 'LATE') AS late_payments,
        COUNT(*) FILTER (WHERE ph.payment_status = 'ON_TIME') AS on_time_payments
    FROM credit_bureau.credit_accounts ca
    LEFT JOIN credit_bureau.payment_history ph
        ON ph.account_id = ca.id
    GROUP BY ca.person_id
)
SELECT
    p.id AS person_id,
    p.national_id,
    p.phone_number,
    p.full_name,
    p.employment_status,
    p.reported_monthly_income,
    COALESCE(a.total_accounts, 0) AS total_accounts,
    COALESCE(a.active_accounts, 0) AS active_accounts,
    COALESCE(a.problematic_accounts, 0) AS problematic_accounts,
    COALESCE(a.total_outstanding_debt, 0) AS total_outstanding_debt,
    COALESCE(a.total_monthly_debt_payment, 0) AS total_monthly_debt_payment,
    COALESCE(a.max_days_past_due, 0) AS max_days_past_due,
    COALESCE(a.overdue_accounts, 0) AS overdue_accounts,
    COALESCE(ps.missed_payments, 0) AS missed_payments,
    COALESCE(ps.late_payments, 0) AS late_payments,
    COALESCE(ps.on_time_payments, 0) AS on_time_payments,
    ls.credit_score,
    ls.risk_level,
    CASE
        WHEN ls.risk_level = 'HIGH' THEN 'OBSERVADO'
        WHEN COALESCE(a.problematic_accounts, 0) > 0 THEN 'OBSERVADO'
        WHEN COALESCE(a.max_days_past_due, 0) > 60 THEN 'OBSERVADO'
        WHEN COALESCE(ps.missed_payments, 0) >= 3 THEN 'OBSERVADO'
        WHEN ls.credit_score IS NOT NULL AND ls.credit_score < 550 THEN 'OBSERVADO'
        ELSE 'APTO'
    END AS preliminary_history_result
FROM credit_bureau.people p
LEFT JOIN account_summary a
    ON a.person_id = p.id
LEFT JOIN payment_summary ps
    ON ps.person_id = p.id
LEFT JOIN latest_score ls
    ON ls.person_id = p.id;

CREATE OR REPLACE FUNCTION credit_bureau.find_profile(identifier TEXT)
RETURNS TABLE (
    national_id VARCHAR,
    phone_number VARCHAR,
    full_name VARCHAR,
    reported_monthly_income NUMERIC,
    total_accounts BIGINT,
    active_accounts BIGINT,
    problematic_accounts BIGINT,
    total_outstanding_debt NUMERIC,
    total_monthly_debt_payment NUMERIC,
    max_days_past_due INTEGER,
    missed_payments BIGINT,
    credit_score INTEGER,
    risk_level VARCHAR,
    preliminary_history_result TEXT
)
LANGUAGE SQL
STABLE
AS $$
    SELECT
        s.national_id,
        s.phone_number,
        s.full_name,
        s.reported_monthly_income,
        s.total_accounts,
        s.active_accounts,
        s.problematic_accounts,
        s.total_outstanding_debt,
        s.total_monthly_debt_payment,
        s.max_days_past_due,
        s.missed_payments,
        s.credit_score,
        s.risk_level,
        s.preliminary_history_result
    FROM credit_bureau.credit_profile_summary s
    WHERE s.national_id = identifier
       OR s.phone_number = identifier
    LIMIT 1;
$$;

INSERT INTO credit_bureau.people (
    national_id,
    phone_number,
    full_name,
    employment_status,
    reported_monthly_income
)
VALUES
    ('9990000001', '+593990000001', 'Andrea Paredes Molina', 'EMPLOYED', 1450),
    ('9990000002', '+593990000002', 'Carlos Zambrano Vera', 'SELF_EMPLOYED', 2100),
    ('9990000003', '+593990000003', 'Maria Torres Cedeno', 'EMPLOYED', 900),
    ('9990000004', '+593990000004', 'Joel Mera Delgado', 'EMPLOYED', 1600),
    ('9990000005', '+593990000005', 'Ana Lopez Moreira', 'EMPLOYED', 1250),
    ('9990000006', '+593990000006', 'Pedro Mendoza Ruiz', 'SELF_EMPLOYED', 2800),
    ('9990000007', '+593990000007', 'Lucia Vera Santos', 'STUDENT', 450),
    ('9990000008', '+593990000008', 'Miguel Cevallos Ortiz', 'RETIRED', 1100),
    ('9990000009', '+593990000009', 'Sofia Alcivar Bravo', 'EMPLOYED', 1750),
    ('9990000010', '+593990000010', 'Diego Macias Loor', 'EMPLOYED', 2400)
ON CONFLICT (national_id) DO UPDATE
SET
    phone_number = EXCLUDED.phone_number,
    full_name = EXCLUDED.full_name,
    employment_status = EXCLUDED.employment_status,
    reported_monthly_income = EXCLUDED.reported_monthly_income,
    updated_at = NOW();

INSERT INTO credit_bureau.credit_accounts (
    person_id,
    institution_name,
    product_type,
    original_amount,
    current_balance,
    monthly_payment,
    status,
    opened_at,
    current_days_past_due,
    max_days_past_due,
    payment_rating
)
VALUES
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000001'), 'Banco Demo Uno', 'PERSONAL_LOAN', 5000, 1700, 240, 'ACTIVE', '2024-02-01', 0, 5, 'A'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000002'), 'Banco Universitario', 'VEHICLE_LOAN', 18000, 9200, 420, 'ACTIVE', '2022-05-15', 0, 15, 'B'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000003'), 'Cooperativa Academica', 'MICROCREDIT', 2500, 2100, 190, 'OVERDUE', '2025-01-08', 75, 90, 'D'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000004'), 'Banco Universitario', 'PERSONAL_LOAN', 3500, 900, 160, 'ACTIVE', '2024-06-20', 0, 0, 'A'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000005'), 'Banco Demo Uno', 'CREDIT_CARD', 2500, 1900, 180, 'OVERDUE', '2022-11-11', 32, 65, 'C'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000006'), 'Banco Universitario', 'MORTGAGE', 45000, 33000, 520, 'ACTIVE', '2020-09-01', 0, 8, 'A')
ON CONFLICT (person_id, institution_name, product_type, opened_at) DO UPDATE
SET
    original_amount = EXCLUDED.original_amount,
    current_balance = EXCLUDED.current_balance,
    monthly_payment = EXCLUDED.monthly_payment,
    status = EXCLUDED.status,
    current_days_past_due = EXCLUDED.current_days_past_due,
    max_days_past_due = EXCLUDED.max_days_past_due,
    payment_rating = EXCLUDED.payment_rating,
    updated_at = NOW();

INSERT INTO credit_bureau.credit_score_snapshots (
    person_id,
    credit_score,
    risk_level
)
VALUES
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000001'), 735, 'LOW'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000002'), 670, 'MEDIUM'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000003'), 485, 'HIGH'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000004'), 760, 'LOW'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000005'), 545, 'HIGH'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000006'), 710, 'LOW')
ON CONFLICT (person_id, credit_score, risk_level) DO NOTHING;

WITH target_account AS (
    SELECT ca.id
    FROM credit_bureau.credit_accounts ca
    JOIN credit_bureau.people p
        ON p.id = ca.person_id
    WHERE p.national_id = '9990000003'
      AND ca.institution_name = 'Cooperativa Academica'
      AND ca.product_type = 'MICROCREDIT'
      AND ca.opened_at = DATE '2025-01-08'
)
INSERT INTO credit_bureau.payment_history (
    account_id,
    period,
    due_amount,
    paid_amount,
    paid_at,
    days_late,
    payment_status
)
SELECT
    target_account.id,
    payment.period,
    payment.due_amount,
    payment.paid_amount,
    payment.paid_at,
    payment.days_late,
    payment.payment_status
FROM target_account
CROSS JOIN (
    VALUES
        (DATE '2025-02-01', 190::NUMERIC, 190::NUMERIC, DATE '2025-02-15', 14, 'LATE'),
        (DATE '2025-03-01', 190::NUMERIC, 0::NUMERIC, NULL::DATE, 30, 'MISSED'),
        (DATE '2025-04-01', 190::NUMERIC, 0::NUMERIC, NULL::DATE, 60, 'MISSED'),
        (DATE '2025-05-01', 190::NUMERIC, 0::NUMERIC, NULL::DATE, 90, 'MISSED')
) AS payment(period, due_amount, paid_amount, paid_at, days_late, payment_status)
ON CONFLICT (account_id, period) DO UPDATE
SET
    due_amount = EXCLUDED.due_amount,
    paid_amount = EXCLUDED.paid_amount,
    paid_at = EXCLUDED.paid_at,
    days_late = EXCLUDED.days_late,
    payment_status = EXCLUDED.payment_status;
