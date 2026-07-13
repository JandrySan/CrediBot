-- Enriquecimiento de central de riesgo simulada para CrediBot.
-- Datos ficticios para pruebas academicas.

ALTER TABLE credit_bureau.people
    ADD COLUMN IF NOT EXISTS identity_type VARCHAR(20) NOT NULL DEFAULT 'CEDULA',
    ADD COLUMN IF NOT EXISTS birth_date DATE,
    ADD COLUMN IF NOT EXISTS gender VARCHAR(20),
    ADD COLUMN IF NOT EXISTS marital_status VARCHAR(30),
    ADD COLUMN IF NOT EXISTS province VARCHAR(80),
    ADD COLUMN IF NOT EXISTS city VARCHAR(80),
    ADD COLUMN IF NOT EXISTS address VARCHAR(180),
    ADD COLUMN IF NOT EXISTS occupation VARCHAR(120),
    ADD COLUMN IF NOT EXISTS employer_name VARCHAR(140),
    ADD COLUMN IF NOT EXISTS job_tenure_months INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS has_ruc BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS dependent_count INTEGER NOT NULL DEFAULT 0;

ALTER TABLE credit_bureau.credit_accounts
    ADD COLUMN IF NOT EXISTS credit_limit NUMERIC(12, 2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS installment_frequency VARCHAR(20) NOT NULL DEFAULT 'MONTHLY',
    ADD COLUMN IF NOT EXISTS collateral_type VARCHAR(80),
    ADD COLUMN IF NOT EXISTS restructured BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS credit_bureau.risk_events (
    id BIGSERIAL PRIMARY KEY,
    person_id UUID NOT NULL
        REFERENCES credit_bureau.people(id)
        ON DELETE CASCADE,
    event_type VARCHAR(40) NOT NULL
        CHECK (
            event_type IN (
                'JUDICIAL_COLLECTION',
                'WRITTEN_OFF',
                'RESTRUCTURED',
                'REFINANCED',
                'FRAUD_ALERT',
                'RETURNED_CHECK',
                'COACTIVE_COLLECTION',
                'BANKRUPTCY',
                'GUARANTOR_DEFAULT'
            )
        ),
    severity VARCHAR(10) NOT NULL
        CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH')),
    source_name VARCHAR(120) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('ACTIVE', 'RESOLVED')),
    occurred_at DATE NOT NULL,
    resolved_at DATE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(person_id, event_type, source_name, occurred_at)
);

CREATE INDEX IF NOT EXISTS idx_risk_events_person
ON credit_bureau.risk_events(person_id);

CREATE INDEX IF NOT EXISTS idx_risk_events_status
ON credit_bureau.risk_events(status);

CREATE TABLE IF NOT EXISTS credit_bureau.credit_inquiries (
    id BIGSERIAL PRIMARY KEY,
    person_id UUID NOT NULL
        REFERENCES credit_bureau.people(id)
        ON DELETE CASCADE,
    institution_name VARCHAR(120) NOT NULL,
    inquiry_reason VARCHAR(60) NOT NULL DEFAULT 'CREDIT_APPLICATION',
    channel VARCHAR(40) NOT NULL DEFAULT 'DIGITAL',
    requested_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(person_id, institution_name, inquiry_reason, created_at)
);

CREATE INDEX IF NOT EXISTS idx_credit_inquiries_person
ON credit_bureau.credit_inquiries(person_id, created_at DESC);

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
    ('9990000001', '+593990000001', 'Andrea Paredes Molina', 'EMPLOYED', 1450, '1992-04-18', 'FEMALE', 'SINGLE', 'Manabi', 'Manta', 'Barrio Universitario', 'Analista contable', 'Comercial Pacifico', 48, false, 0),
    ('9990000002', '+593990000002', 'Carlos Zambrano Vera', 'SELF_EMPLOYED', 2100, '1988-09-03', 'MALE', 'MARRIED', 'Manabi', 'Portoviejo', 'Av. Reales Tamarindos', 'Comerciante', 'Negocio propio', 72, true, 2),
    ('9990000003', '+593990000003', 'María Torres Cedeño', 'EMPLOYED', 900, '1996-01-27', 'FEMALE', 'SINGLE', 'Manabi', 'Manta', 'Los Esteros', 'Asistente administrativa', 'Servicios del Puerto', 14, false, 1),
    ('9990000004', '+593990000004', 'Joel Mera Delgado', 'EMPLOYED', 1600, '1990-11-12', 'MALE', 'MARRIED', 'Manabi', 'Manta', 'Urb. Barbasquillo', 'Tecnico industrial', 'Astillero Demo', 60, false, 2),
    ('9990000005', '+593990000005', 'Ana López Moreira', 'EMPLOYED', 1250, '1985-06-21', 'FEMALE', 'DIVORCED', 'Guayas', 'Guayaquil', 'Alborada', 'Supervisora de ventas', 'Retail Demo', 36, false, 2),
    ('9990000006', '+593990000006', 'Pedro Mendoza Ruiz', 'SELF_EMPLOYED', 2800, '1979-02-07', 'MALE', 'MARRIED', 'Pichincha', 'Quito', 'La Carolina', 'Arquitecto independiente', 'Estudio Mendoza', 120, true, 3),
    ('9990000007', '+593990000007', 'Lucía Vera Santos', 'STUDENT', 450, '2003-10-02', 'FEMALE', 'SINGLE', 'Manabi', 'Manta', 'Tarqui', 'Estudiante', 'N/A', 0, false, 0),
    ('9990000008', '+593990000008', 'Miguel Cevallos Ortiz', 'RETIRED', 1100, '1964-03-15', 'MALE', 'MARRIED', 'Manabi', 'Montecristi', 'Centro', 'Jubilado', 'IESS', 0, false, 1),
    ('9990000009', '+593990000009', 'Sofía Alcívar Bravo', 'EMPLOYED', 1750, '1994-08-28', 'FEMALE', 'SINGLE', 'Manabi', 'Jaramijo', 'Via al puerto', 'Ingeniera de procesos', 'Atunera Demo', 42, false, 0),
    ('9990000010', '+593990000010', 'Diego Macías Loor', 'EMPLOYED', 2400, '1987-12-09', 'MALE', 'MARRIED', 'Manabi', 'Manta', 'Via San Mateo', 'Coordinador logistico', 'Operador Portuario Demo', 84, false, 1),
    ('9990000011', '+593990000011', 'Valeria Zamora Rivas', 'EMPLOYED', 680, '2000-05-19', 'FEMALE', 'SINGLE', 'Esmeraldas', 'Esmeraldas', 'Las Palmas', 'Cajera', 'Minimarket Demo', 8, false, 1),
    ('9990000012', '+593990000012', 'Hugo Andrade Cevallos', 'SELF_EMPLOYED', 3200, '1982-07-30', 'MALE', 'MARRIED', 'Pichincha', 'Quito', 'Cumbaya', 'Consultor tecnologico', 'Servicios Andrade', 96, true, 2),
    ('9990000013', '+593990000013', 'Karina Saltos Pinargote', 'EMPLOYED', 1150, '1998-09-22', 'FEMALE', 'SINGLE', 'Manabi', 'Chone', 'Centro', 'Docente', 'Unidad Educativa Demo', 30, false, 0),
    ('9990000014', '+593990000014', 'Roberto Quiroz Velez', 'UNEMPLOYED', 300, '1991-01-14', 'MALE', 'SINGLE', 'Guayas', 'Duran', 'Primavera', 'Sin empleo fijo', 'N/A', 0, false, 2),
    ('9990000015', '+593990000015', 'Nadia Delgado Zambrano', 'EMPLOYED', 1950, '1989-11-05', 'FEMALE', 'MARRIED', 'Manabi', 'Manta', 'Ciudadela Universitaria', 'Medica general', 'Clinica Demo', 54, false, 1)
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
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000001'), 'Banco Demo Uno', 'PERSONAL_LOAN', 5000, 0, 1700, 240, 'ACTIVE', '2024-02-01', 0, 5, 'A', 'SIN GARANTIA', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000001'), 'Tarjeta Demo', 'CREDIT_CARD', 0, 2500, 480, 80, 'ACTIVE', '2023-03-10', 0, 0, 'A', NULL, false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000002'), 'Banco Universitario', 'VEHICLE_LOAN', 18000, 0, 9200, 420, 'ACTIVE', '2022-05-15', 0, 15, 'B', 'VEHICULO', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000003'), 'Cooperativa Academica', 'MICROCREDIT', 2500, 0, 2100, 190, 'OVERDUE', '2025-01-08', 75, 90, 'D', 'GARANTE', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000004'), 'Banco Universitario', 'PERSONAL_LOAN', 3500, 0, 900, 160, 'ACTIVE', '2024-06-20', 0, 0, 'A', 'SIN GARANTIA', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000005'), 'Banco Demo Uno', 'CREDIT_CARD', 2500, 2500, 1900, 180, 'OVERDUE', '2022-11-11', 32, 65, 'C', NULL, true),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000005'), 'Casa Comercial Demo', 'STORE_CREDIT', 1200, 0, 0, 0, 'WRITTEN_OFF', '2021-02-02', 0, 120, 'E', NULL, false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000006'), 'Banco Universitario', 'MORTGAGE', 45000, 0, 33000, 520, 'ACTIVE', '2020-09-01', 0, 8, 'A', 'HIPOTECA', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000008'), 'Cooperativa Senior', 'PERSONAL_LOAN', 1500, 0, 350, 110, 'ACTIVE', '2025-02-10', 0, 0, 'A', 'SIN GARANTIA', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000009'), 'Tarjeta Demo', 'CREDIT_CARD', 0, 4000, 760, 130, 'ACTIVE', '2022-08-12', 0, 10, 'A', NULL, false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000010'), 'Banco Pacifico Demo', 'VEHICLE_LOAN', 22000, 0, 7600, 390, 'ACTIVE', '2023-07-19', 0, 0, 'A', 'VEHICULO', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000011'), 'Financiera Rapida', 'MICROCREDIT', 900, 0, 720, 120, 'ACTIVE', '2025-03-01', 18, 18, 'C', 'SIN GARANTIA', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000012'), 'Banco Empresarial', 'PERSONAL_LOAN', 12000, 0, 2800, 360, 'ACTIVE', '2023-01-15', 0, 0, 'A', 'SIN GARANTIA', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000012'), 'Tarjeta Premium', 'CREDIT_CARD', 0, 8000, 1200, 180, 'ACTIVE', '2021-04-05', 0, 0, 'A', NULL, false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000013'), 'Cooperativa Educadores', 'PERSONAL_LOAN', 2400, 0, 600, 150, 'ACTIVE', '2024-09-01', 0, 0, 'B', 'ROL DE PAGOS', false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000014'), 'Casa Comercial Demo', 'STORE_CREDIT', 1800, 0, 1600, 150, 'OVERDUE', '2023-04-17', 110, 150, 'E', NULL, false),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000015'), 'Banco Salud', 'PERSONAL_LOAN', 6000, 0, 1800, 260, 'ACTIVE', '2024-01-10', 0, 0, 'A', 'SIN GARANTIA', false)
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
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000007'), 610, 'MEDIUM'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000008'), 690, 'MEDIUM'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000009'), 720, 'LOW'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000010'), 705, 'LOW'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000011'), 560, 'MEDIUM'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000012'), 790, 'LOW'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000013'), 650, 'MEDIUM'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000014'), 420, 'HIGH'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000015'), 748, 'LOW')
ON CONFLICT (person_id, credit_score, risk_level) DO NOTHING;

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
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000003'), 'COACTIVE_COLLECTION', 'HIGH', 'Cooperativa Academica', 2100, 'ACTIVE', '2025-05-01', NULL, 'Mora superior a 60 dias en microcredito'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000005'), 'RESTRUCTURED', 'MEDIUM', 'Banco Demo Uno', 1900, 'ACTIVE', '2024-12-01', NULL, 'Tarjeta reestructurada con mora recurrente'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000005'), 'WRITTEN_OFF', 'HIGH', 'Casa Comercial Demo', 1200, 'ACTIVE', '2023-09-15', NULL, 'Credito comercial castigado'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000011'), 'REFINANCED', 'LOW', 'Financiera Rapida', 720, 'ACTIVE', '2025-05-15', NULL, 'Refinanciamiento preventivo'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000014'), 'JUDICIAL_COLLECTION', 'HIGH', 'Casa Comercial Demo', 1600, 'ACTIVE', '2025-01-20', NULL, 'Cobranza judicial por mora severa'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000014'), 'RETURNED_CHECK', 'MEDIUM', 'Banco Local', 280, 'RESOLVED', '2024-02-10', '2024-04-20', 'Cheque protestado regularizado')
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
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000003'), 'Fintech Demo', 'CREDIT_APPLICATION', 'DIGITAL', 1200, NOW() - INTERVAL '20 days'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000003'), 'Banco Demo Uno', 'CREDIT_APPLICATION', 'BRANCH', 2000, NOW() - INTERVAL '75 days'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000005'), 'Retail Demo', 'CREDIT_APPLICATION', 'DIGITAL', 800, NOW() - INTERVAL '40 days'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000011'), 'Financiera Rapida', 'CREDIT_APPLICATION', 'DIGITAL', 700, NOW() - INTERVAL '12 days'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000014'), 'Cooperativa Demo', 'CREDIT_APPLICATION', 'DIGITAL', 1000, NOW() - INTERVAL '8 days'),
    ((SELECT id FROM credit_bureau.people WHERE national_id = '9990000014'), 'Casa Comercial Demo', 'CREDIT_APPLICATION', 'STORE', 600, NOW() - INTERVAL '35 days');

DROP FUNCTION IF EXISTS credit_bureau.find_profile(TEXT);
DROP VIEW IF EXISTS credit_bureau.credit_profile_summary;

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
        COUNT(*) FILTER (WHERE status = 'WRITTEN_OFF') AS written_off_accounts,
        COUNT(*) FILTER (WHERE restructured IS TRUE) AS restructured_accounts,
        COALESCE(SUM(current_balance) FILTER (WHERE status IN ('ACTIVE', 'OVERDUE')), 0)
            AS total_outstanding_debt,
        COALESCE(SUM(monthly_payment) FILTER (WHERE status IN ('ACTIVE', 'OVERDUE')), 0)
            AS total_monthly_debt_payment,
        COALESCE(MAX(max_days_past_due), 0) AS max_days_past_due,
        COUNT(*) FILTER (WHERE current_days_past_due > 0) AS overdue_accounts,
        COALESCE(
            ROUND(
                100 * SUM(current_balance) FILTER (WHERE product_type = 'CREDIT_CARD')
                / NULLIF(SUM(credit_limit) FILTER (WHERE product_type = 'CREDIT_CARD'), 0),
                2
            ),
            0
        ) AS credit_card_utilization_percent
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
),
risk_summary AS (
    SELECT
        person_id,
        COUNT(*) FILTER (WHERE status = 'ACTIVE') AS active_risk_events,
        COUNT(*) FILTER (WHERE status = 'ACTIVE' AND event_type = 'JUDICIAL_COLLECTION') AS judicial_collection_events,
        COUNT(*) FILTER (WHERE status = 'ACTIVE' AND event_type = 'WRITTEN_OFF') AS written_off_events,
        COUNT(*) FILTER (WHERE status = 'ACTIVE' AND severity = 'HIGH') AS high_severity_events,
        STRING_AGG(notes, '; ' ORDER BY occurred_at DESC) FILTER (WHERE status = 'ACTIVE') AS active_risk_notes
    FROM credit_bureau.risk_events
    GROUP BY person_id
),
inquiry_summary AS (
    SELECT
        person_id,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '6 months') AS recent_inquiries_6m
    FROM credit_bureau.credit_inquiries
    GROUP BY person_id
)
SELECT
    p.id AS person_id,
    p.national_id,
    p.phone_number,
    p.full_name,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.birth_date))::INTEGER AS age,
    p.gender,
    p.marital_status,
    p.province,
    p.city,
    p.employment_status,
    p.occupation,
    p.employer_name,
    p.job_tenure_months,
    p.has_ruc,
    p.dependent_count,
    p.reported_monthly_income,
    COALESCE(a.total_accounts, 0) AS total_accounts,
    COALESCE(a.active_accounts, 0) AS active_accounts,
    COALESCE(a.problematic_accounts, 0) AS problematic_accounts,
    COALESCE(a.written_off_accounts, 0) AS written_off_accounts,
    COALESCE(a.restructured_accounts, 0) AS restructured_accounts,
    COALESCE(a.total_outstanding_debt, 0) AS total_outstanding_debt,
    COALESCE(a.total_monthly_debt_payment, 0) AS total_monthly_debt_payment,
    ROUND(COALESCE(a.total_monthly_debt_payment, 0) / NULLIF(p.reported_monthly_income, 0), 4)
        AS debt_to_income_ratio,
    GREATEST(ROUND((p.reported_monthly_income * 0.35) - COALESCE(a.total_monthly_debt_payment, 0), 2), 0)
        AS recommended_max_installment,
    COALESCE(a.credit_card_utilization_percent, 0) AS credit_card_utilization_percent,
    COALESCE(a.max_days_past_due, 0) AS max_days_past_due,
    COALESCE(a.overdue_accounts, 0) AS overdue_accounts,
    COALESCE(ps.missed_payments, 0) AS missed_payments,
    COALESCE(ps.late_payments, 0) AS late_payments,
    COALESCE(ps.on_time_payments, 0) AS on_time_payments,
    COALESCE(rs.active_risk_events, 0) AS active_risk_events,
    COALESCE(rs.judicial_collection_events, 0) AS judicial_collection_events,
    COALESCE(rs.written_off_events, 0) AS written_off_events,
    COALESCE(rs.high_severity_events, 0) AS high_severity_events,
    COALESCE(iq.recent_inquiries_6m, 0) AS recent_inquiries_6m,
    ls.credit_score,
    ls.risk_level,
    CASE
        WHEN COALESCE(rs.high_severity_events, 0) > 0
          OR COALESCE(rs.judicial_collection_events, 0) > 0
          OR COALESCE(rs.written_off_events, 0) > 0
          OR COALESCE(a.written_off_accounts, 0) > 0
            THEN 'NEGATIVE'
        WHEN ls.risk_level = 'HIGH'
          OR COALESCE(a.problematic_accounts, 0) > 0
          OR COALESCE(a.max_days_past_due, 0) > 60
          OR COALESCE(ps.missed_payments, 0) >= 3
          OR COALESCE(a.credit_card_utilization_percent, 0) > 85
          OR COALESCE(iq.recent_inquiries_6m, 0) >= 4
            THEN 'WATCHLIST'
        ELSE 'CLEAR'
    END AS central_risk_status,
    NULLIF(
        CONCAT_WS(
            '; ',
            CASE WHEN COALESCE(rs.high_severity_events, 0) > 0 THEN 'Eventos severos activos en central' END,
            CASE WHEN COALESCE(rs.judicial_collection_events, 0) > 0 THEN 'Cobranza judicial/coactiva activa' END,
            CASE WHEN COALESCE(rs.written_off_events, 0) > 0 OR COALESCE(a.written_off_accounts, 0) > 0 THEN 'Obligaciones castigadas' END,
            CASE WHEN COALESCE(a.max_days_past_due, 0) > 60 THEN 'Mora historica mayor a 60 dias' END,
            CASE WHEN COALESCE(ps.missed_payments, 0) >= 3 THEN 'Tres o mas pagos incumplidos' END,
            CASE WHEN COALESCE(a.credit_card_utilization_percent, 0) > 85 THEN 'Alta utilizacion de tarjeta' END,
            rs.active_risk_notes
        ),
        ''
    ) AS central_risk_reason,
    CASE
        WHEN COALESCE(rs.high_severity_events, 0) > 0
          OR COALESCE(rs.judicial_collection_events, 0) > 0
          OR COALESCE(rs.written_off_events, 0) > 0
          OR COALESCE(a.written_off_accounts, 0) > 0
          OR ls.risk_level = 'HIGH'
          OR COALESCE(a.problematic_accounts, 0) > 0
          OR COALESCE(a.max_days_past_due, 0) > 60
          OR COALESCE(ps.missed_payments, 0) >= 3
          OR (ls.credit_score IS NOT NULL AND ls.credit_score < 550)
            THEN 'OBSERVADO'
        ELSE 'APTO'
    END AS preliminary_history_result
FROM credit_bureau.people p
LEFT JOIN account_summary a
    ON a.person_id = p.id
LEFT JOIN payment_summary ps
    ON ps.person_id = p.id
LEFT JOIN risk_summary rs
    ON rs.person_id = p.id
LEFT JOIN inquiry_summary iq
    ON iq.person_id = p.id
LEFT JOIN latest_score ls
    ON ls.person_id = p.id;

CREATE OR REPLACE FUNCTION credit_bureau.find_profile(identifier TEXT)
RETURNS TABLE (
    national_id VARCHAR,
    phone_number VARCHAR,
    full_name VARCHAR,
    age INTEGER,
    province VARCHAR,
    city VARCHAR,
    employment_status VARCHAR,
    occupation VARCHAR,
    reported_monthly_income NUMERIC,
    central_risk_status TEXT,
    central_risk_reason TEXT,
    total_accounts BIGINT,
    active_accounts BIGINT,
    problematic_accounts BIGINT,
    total_outstanding_debt NUMERIC,
    total_monthly_debt_payment NUMERIC,
    debt_to_income_ratio NUMERIC,
    max_days_past_due INTEGER,
    missed_payments BIGINT,
    late_payments BIGINT,
    written_off_accounts BIGINT,
    judicial_collection_events BIGINT,
    restructured_accounts BIGINT,
    recent_inquiries_6m BIGINT,
    recommended_max_installment NUMERIC,
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
        s.age,
        s.province,
        s.city,
        s.employment_status,
        s.occupation,
        s.reported_monthly_income,
        s.central_risk_status,
        s.central_risk_reason,
        s.total_accounts,
        s.active_accounts,
        s.problematic_accounts,
        s.total_outstanding_debt,
        s.total_monthly_debt_payment,
        s.debt_to_income_ratio,
        s.max_days_past_due,
        s.missed_payments,
        s.late_payments,
        s.written_off_accounts,
        s.judicial_collection_events,
        s.restructured_accounts,
        s.recent_inquiries_6m,
        s.recommended_max_installment,
        s.credit_score,
        s.risk_level,
        s.preliminary_history_result
    FROM credit_bureau.credit_profile_summary s
    WHERE s.national_id = identifier
       OR s.phone_number = identifier
    LIMIT 1;
$$;
