-- CrediBot - perfiles faciles para demo de central de riesgo.
-- Datos ficticios. No representan informacion real de los colaboradores.

INSERT INTO credit_bureau.people (
    national_id,
    phone_number,
    full_name,
    employment_status,
    reported_monthly_income,
    birth_date,
    gender,
    marital_status,
    province,
    city,
    address,
    occupation,
    employer_name,
    job_tenure_months,
    has_ruc,
    dependent_count
)
VALUES
    ('1111111111', '+593911111111', 'Diego Calva Ortiz', 'EMPLOYED', 2600, '1995-07-13', 'MALE', 'SINGLE', 'Manabi', 'Manta', 'Centro', 'Ingeniero de software', 'CrediBot Demo', 48, false, 0),
    ('2222222222', '+593922222222', 'Jandry San Mendoza', 'SELF_EMPLOYED', 1850, '1994-03-22', 'MALE', 'SINGLE', 'Manabi', 'Manta', 'Tarqui', 'Desarrollador independiente', 'Servicios Jandry Demo', 36, true, 1),
    ('3333333333', '+593933333333', 'Joel Andrade Briones', 'EMPLOYED', 980, '1998-11-04', 'MALE', 'SINGLE', 'Manabi', 'Portoviejo', 'Andres de Vera', 'Analista de soporte', 'Mesa Tecnica Demo', 18, false, 0),
    ('4444444444', '+593944444444', 'Carlos Duty Zambrano', 'UNEMPLOYED', 360, '1996-05-19', 'MALE', 'SINGLE', 'Guayas', 'Guayaquil', 'Sauces', 'Sin empleo fijo', 'N/A', 0, false, 2),
    ('5555555555', '+593955555555', 'Maria Jose Cedeño Lopez', 'EMPLOYED', 1350, '1992-09-16', 'FEMALE', 'MARRIED', 'Manabi', 'Manta', 'Barbasquillo', 'Supervisora comercial', 'Retail Costa Demo', 40, false, 1),
    ('6666666666', '+593966666666', 'Andrea Solorzano Vera', 'STUDENT', 520, '2002-01-09', 'FEMALE', 'SINGLE', 'Manabi', 'Manta', 'Universitaria', 'Estudiante', 'N/A', 0, false, 0),
    ('7777777777', '+593977777777', 'Hugo Valencia Rivas', 'RETIRED', 1150, '1962-12-30', 'MALE', 'MARRIED', 'Pichincha', 'Quito', 'La Floresta', 'Jubilado', 'IESS', 0, false, 1),
    ('8888888888', '+593988888888', 'Karina Delgado Moreira', 'SELF_EMPLOYED', 3100, '1987-06-24', 'FEMALE', 'MARRIED', 'Guayas', 'Duran', 'Primavera', 'Comerciante mayorista', 'Comercial Karina Demo', 96, true, 3)
ON CONFLICT (national_id) DO UPDATE
SET
    phone_number = EXCLUDED.phone_number,
    full_name = EXCLUDED.full_name,
    employment_status = EXCLUDED.employment_status,
    reported_monthly_income = EXCLUDED.reported_monthly_income,
    birth_date = EXCLUDED.birth_date,
    gender = EXCLUDED.gender,
    marital_status = EXCLUDED.marital_status,
    province = EXCLUDED.province,
    city = EXCLUDED.city,
    address = EXCLUDED.address,
    occupation = EXCLUDED.occupation,
    employer_name = EXCLUDED.employer_name,
    job_tenure_months = EXCLUDED.job_tenure_months,
    has_ruc = EXCLUDED.has_ruc,
    dependent_count = EXCLUDED.dependent_count,
    updated_at = NOW();

INSERT INTO credit_bureau.credit_accounts (
    person_id,
    institution_name,
    product_type,
    original_amount,
    credit_limit,
    current_balance,
    monthly_payment,
    status,
    opened_at,
    current_days_past_due,
    max_days_past_due,
    payment_rating,
    collateral_type,
    restructured
)
VALUES
    ((SELECT id FROM credit_bureau.people WHERE national_id = '1111111111'), 'Banco Demo Uno', 'PERSONAL_LOAN', 7000, 0, 1800, 290, 'ACTIVE', '2024-01-15', 0, 0, 'A', 'SIN GARANTIA', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '1111111111'), 'Tarjeta Demo', 'CREDIT_CARD', 0, 4500, 620, 95, 'ACTIVE', '2023-04-11', 0, 0, 'A', NULL, false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '2222222222'), 'Cooperativa Emprende', 'MICROCREDIT', 3500, 0, 1200, 180, 'ACTIVE', '2024-08-01', 0, 25, 'B', 'GARANTE', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '3333333333'), 'Tarjeta Demo', 'CREDIT_CARD', 0, 1000, 940, 120, 'ACTIVE', '2024-05-20', 0, 35, 'C', NULL, false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '3333333333'), 'Financiera Rapida', 'MICROCREDIT', 1200, 0, 860, 105, 'OVERDUE', '2025-02-01', 45, 65, 'D', 'SIN GARANTIA', true),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '4444444444'), 'Casa Comercial Demo', 'STORE_CREDIT', 1600, 0, 1450, 130, 'OVERDUE', '2023-10-10', 120, 150, 'E', NULL, false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '5555555555'), 'Banco Demo Uno', 'PERSONAL_LOAN', 3200, 0, 700, 150, 'ACTIVE', '2024-09-12', 0, 0, 'A', 'ROL DE PAGOS', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '6666666666'), 'Tienda Universitaria', 'STORE_CREDIT', 500, 0, 220, 45, 'ACTIVE', '2025-04-01', 0, 10, 'B', NULL, false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '7777777777'), 'Cooperativa Senior', 'PERSONAL_LOAN', 2000, 0, 500, 110, 'ACTIVE', '2024-11-01', 0, 0, 'A', 'SIN GARANTIA', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '8888888888'), 'Banco Empresarial', 'PERSONAL_LOAN', 18000, 0, 7600, 520, 'ACTIVE', '2022-03-15', 0, 12, 'B', 'GARANTE', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '8888888888'), 'Tarjeta Premium', 'CREDIT_CARD', 0, 9000, 6100, 310, 'ACTIVE', '2021-08-09', 0, 0, 'A', NULL, false)
ON CONFLICT (person_id, institution_name, product_type, opened_at) DO UPDATE
SET
    original_amount = EXCLUDED.original_amount,
    credit_limit = EXCLUDED.credit_limit,
    current_balance = EXCLUDED.current_balance,
    monthly_payment = EXCLUDED.monthly_payment,
    status = EXCLUDED.status,
    current_days_past_due = EXCLUDED.current_days_past_due,
    max_days_past_due = EXCLUDED.max_days_past_due,
    payment_rating = EXCLUDED.payment_rating,
    collateral_type = EXCLUDED.collateral_type,
    restructured = EXCLUDED.restructured,
    updated_at = NOW();

INSERT INTO credit_bureau.credit_score_snapshots (person_id, credit_score, risk_level)
VALUES
    ((SELECT id FROM credit_bureau.people WHERE national_id = '1111111111'), 805, 'LOW'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '2222222222'), 682, 'MEDIUM'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '3333333333'), 540, 'HIGH'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '4444444444'), 405, 'HIGH'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '5555555555'), 735, 'LOW'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '6666666666'), 610, 'MEDIUM'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '7777777777'), 700, 'LOW'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '8888888888'), 665, 'MEDIUM')
ON CONFLICT (person_id, credit_score, risk_level) DO NOTHING;

WITH payment_seed AS (
    SELECT
        ca.id AS account_id,
        p.national_id,
        seed.period,
        seed.due_amount,
        seed.paid_amount,
        seed.paid_at,
        seed.days_late,
        seed.payment_status
    FROM credit_bureau.people p
    JOIN credit_bureau.credit_accounts ca
        ON ca.person_id = p.id
    JOIN (
        VALUES
            ('1111111111', 'Banco Demo Uno', 'PERSONAL_LOAN', DATE '2025-02-01', 290::NUMERIC, 290::NUMERIC, DATE '2025-02-02', 1, 'ON_TIME'),
            ('1111111111', 'Banco Demo Uno', 'PERSONAL_LOAN', DATE '2025-03-01', 290::NUMERIC, 290::NUMERIC, DATE '2025-03-01', 0, 'ON_TIME'),
            ('2222222222', 'Cooperativa Emprende', 'MICROCREDIT', DATE '2025-03-01', 180::NUMERIC, 180::NUMERIC, DATE '2025-03-18', 17, 'LATE'),
            ('3333333333', 'Financiera Rapida', 'MICROCREDIT', DATE '2025-03-01', 105::NUMERIC, 0::NUMERIC, NULL::DATE, 30, 'MISSED'),
            ('3333333333', 'Financiera Rapida', 'MICROCREDIT', DATE '2025-04-01', 105::NUMERIC, 0::NUMERIC, NULL::DATE, 60, 'MISSED'),
            ('3333333333', 'Financiera Rapida', 'MICROCREDIT', DATE '2025-05-01', 105::NUMERIC, 0::NUMERIC, NULL::DATE, 65, 'MISSED'),
            ('4444444444', 'Casa Comercial Demo', 'STORE_CREDIT', DATE '2025-01-01', 130::NUMERIC, 0::NUMERIC, NULL::DATE, 90, 'MISSED'),
            ('4444444444', 'Casa Comercial Demo', 'STORE_CREDIT', DATE '2025-02-01', 130::NUMERIC, 0::NUMERIC, NULL::DATE, 120, 'MISSED'),
            ('5555555555', 'Banco Demo Uno', 'PERSONAL_LOAN', DATE '2025-04-01', 150::NUMERIC, 150::NUMERIC, DATE '2025-04-01', 0, 'ON_TIME'),
            ('6666666666', 'Tienda Universitaria', 'STORE_CREDIT', DATE '2025-05-01', 45::NUMERIC, 45::NUMERIC, DATE '2025-05-05', 4, 'ON_TIME'),
            ('7777777777', 'Cooperativa Senior', 'PERSONAL_LOAN', DATE '2025-05-01', 110::NUMERIC, 110::NUMERIC, DATE '2025-05-01', 0, 'ON_TIME'),
            ('8888888888', 'Banco Empresarial', 'PERSONAL_LOAN', DATE '2025-04-01', 520::NUMERIC, 520::NUMERIC, DATE '2025-04-10', 9, 'ON_TIME')
    ) AS seed(national_id, institution_name, product_type, period, due_amount, paid_amount, paid_at, days_late, payment_status)
        ON seed.national_id = p.national_id
       AND seed.institution_name = ca.institution_name
       AND seed.product_type = ca.product_type
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
    account_id,
    period,
    due_amount,
    paid_amount,
    paid_at,
    days_late,
    payment_status
FROM payment_seed
ON CONFLICT (account_id, period) DO UPDATE
SET
    due_amount = EXCLUDED.due_amount,
    paid_amount = EXCLUDED.paid_amount,
    paid_at = EXCLUDED.paid_at,
    days_late = EXCLUDED.days_late,
    payment_status = EXCLUDED.payment_status;

INSERT INTO credit_bureau.risk_events (
    person_id,
    event_type,
    severity,
    source_name,
    amount,
    status,
    occurred_at,
    resolved_at,
    notes
)
VALUES
    ((SELECT id FROM credit_bureau.people WHERE national_id = '3333333333'), 'RESTRUCTURED', 'MEDIUM', 'Financiera Rapida', 860, 'ACTIVE', '2025-05-15', NULL, 'Credito reestructurado por mora recurrente'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '4444444444'), 'JUDICIAL_COLLECTION', 'HIGH', 'Casa Comercial Demo', 1450, 'ACTIVE', '2025-03-20', NULL, 'Cobranza judicial activa por mora severa'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '4444444444'), 'RETURNED_CHECK', 'MEDIUM', 'Banco Local', 320, 'RESOLVED', '2024-10-02', '2024-12-15', 'Cheque protestado regularizado')
ON CONFLICT (person_id, event_type, source_name, occurred_at) DO UPDATE
SET
    severity = EXCLUDED.severity,
    amount = EXCLUDED.amount,
    status = EXCLUDED.status,
    resolved_at = EXCLUDED.resolved_at,
    notes = EXCLUDED.notes;

INSERT INTO credit_bureau.credit_inquiries (
    person_id,
    institution_name,
    inquiry_reason,
    channel,
    requested_amount,
    created_at
)
VALUES
    ((SELECT id FROM credit_bureau.people WHERE national_id = '2222222222'), 'Fintech Demo', 'CREDIT_APPLICATION', 'DIGITAL', 1200, TIMESTAMPTZ '2026-06-20 10:00:00+00'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '3333333333'), 'Banco Demo Uno', 'CREDIT_APPLICATION', 'DIGITAL', 900, TIMESTAMPTZ '2026-06-18 10:00:00+00'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '3333333333'), 'Casa Comercial Demo', 'CREDIT_APPLICATION', 'STORE', 600, TIMESTAMPTZ '2026-06-28 10:00:00+00'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '4444444444'), 'Cooperativa Demo', 'CREDIT_APPLICATION', 'DIGITAL', 1000, TIMESTAMPTZ '2026-06-30 10:00:00+00'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '8888888888'), 'Banco Empresarial', 'CREDIT_APPLICATION', 'BRANCH', 5000, TIMESTAMPTZ '2026-06-10 10:00:00+00')
ON CONFLICT (person_id, institution_name, inquiry_reason, created_at) DO UPDATE
SET
    channel = EXCLUDED.channel,
    requested_amount = EXCLUDED.requested_amount;
