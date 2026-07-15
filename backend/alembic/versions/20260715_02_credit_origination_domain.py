"""Agrega el dominio versionado de originacion crediticia."""

from alembic import op
import sqlalchemy as sa


revision = "20260715_02"
down_revision = "20260715_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    _create_product_catalog(bind)
    _create_policy_tables(bind)
    _upgrade_credit_applications(bind)
    _create_operational_tables(bind)
    _upgrade_credit_bureau(bind)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS credit_bureau.idx_people_dataset_batch")
        op.execute("ALTER TABLE IF EXISTS credit_bureau.people DROP COLUMN IF EXISTS pep_status")
        op.execute(
            "ALTER TABLE IF EXISTS credit_bureau.people "
            "DROP COLUMN IF EXISTS income_verification_status"
        )
        op.execute(
            "ALTER TABLE IF EXISTS credit_bureau.people "
            "DROP COLUMN IF EXISTS identity_verified"
        )
        op.execute(
            "ALTER TABLE IF EXISTS credit_bureau.people DROP COLUMN IF EXISTS source_of_funds"
        )
        op.execute(
            "ALTER TABLE IF EXISTS credit_bureau.people DROP COLUMN IF EXISTS liabilities_total"
        )
        op.execute(
            "ALTER TABLE IF EXISTS credit_bureau.people DROP COLUMN IF EXISTS assets_total"
        )
        op.execute(
            "ALTER TABLE IF EXISTS credit_bureau.people DROP COLUMN IF EXISTS housing_status"
        )
        op.execute(
            "ALTER TABLE IF EXISTS credit_bureau.people "
            "DROP COLUMN IF EXISTS monthly_living_expenses"
        )
        op.execute(
            "ALTER TABLE IF EXISTS credit_bureau.people "
            "DROP COLUMN IF EXISTS other_monthly_income"
        )
        op.execute(
            "ALTER TABLE IF EXISTS credit_bureau.people "
            "DROP COLUMN IF EXISTS business_tenure_months"
        )
        op.execute(
            "ALTER TABLE IF EXISTS credit_bureau.people DROP COLUMN IF EXISTS economic_activity"
        )
        op.execute(
            "ALTER TABLE IF EXISTS credit_bureau.people DROP COLUMN IF EXISTS synthetic_key"
        )
        op.execute(
            "ALTER TABLE IF EXISTS credit_bureau.people DROP COLUMN IF EXISTS is_synthetic"
        )
        op.execute(
            "ALTER TABLE IF EXISTS credit_bureau.people DROP COLUMN IF EXISTS dataset_batch_id"
        )
        op.execute("DROP TABLE IF EXISTS credit_bureau.dataset_batches")

    for table in (
        "credit_decisions",
        "application_documents",
        "consent_records",
        "conversation_contexts",
        "customer_financial_profiles",
    ):
        if sa.inspect(bind).has_table(table):
            op.drop_table(table)

    application_indexes = {
        index["name"] for index in sa.inspect(bind).get_indexes("credit_applications")
    }
    for index_name in (
        "ix_credit_applications_product_id",
        "ix_credit_applications_status",
    ):
        if index_name in application_indexes:
            op.drop_index(index_name, table_name="credit_applications")

    application_columns = _column_names(bind, "credit_applications")
    removable_columns = [
        column
        for column in (
        "updated_at",
        "status",
        "amortization_type",
        "requested_payment_day",
        "purpose",
        "product_id",
        )
        if column in application_columns
    ]
    if bind.dialect.name == "sqlite" and removable_columns:
        with op.batch_alter_table("credit_applications") as batch_op:
            for column in removable_columns:
                batch_op.drop_column(column)
    else:
        for column in removable_columns:
            op.drop_column("credit_applications", column)

    for table in (
        "credit_policy_rules",
        "credit_policy_versions",
        "credit_product_requirements",
        "credit_products",
    ):
        if sa.inspect(bind).has_table(table):
            op.drop_table(table)


def _create_product_catalog(bind) -> None:
    if not sa.inspect(bind).has_table("credit_products"):
        op.create_table(
            "credit_products",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(50), nullable=False, unique=True),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column("segment", sa.String(50), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
            sa.Column("min_amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("max_amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("min_term_months", sa.Integer(), nullable=False),
            sa.Column("max_term_months", sa.Integer(), nullable=False),
            sa.Column("effective_annual_rate", sa.Numeric(8, 4), nullable=False),
            sa.Column("max_effective_annual_rate", sa.Numeric(8, 4), nullable=False),
            sa.Column(
                "amortization_type", sa.String(20), nullable=False, server_default="FRENCH"
            ),
            sa.Column(
                "payment_frequency", sa.String(20), nullable=False, server_default="MONTHLY"
            ),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("source_url", sa.Text()),
            sa.Column("effective_from", sa.Date(), nullable=False),
            sa.Column("effective_to", sa.Date()),
            sa.Column(
                "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
            ),
            sa.Column("updated_at", sa.DateTime(timezone=True)),
        )
        op.create_index("ix_credit_products_code", "credit_products", ["code"])
        op.create_index("ix_credit_products_segment", "credit_products", ["segment"])

    if not sa.inspect(bind).has_table("credit_product_requirements"):
        op.create_table(
            "credit_product_requirements",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "product_id",
                sa.Integer(),
                sa.ForeignKey("credit_products.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("code", sa.String(60), nullable=False),
            sa.Column("name", sa.String(140), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("applicant_type", sa.String(30), nullable=False, server_default="ALL"),
            sa.Column("requirement_type", sa.String(30), nullable=False),
            sa.Column("stage", sa.String(30), nullable=False, server_default="APPLICATION"),
            sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("conditions", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.UniqueConstraint("product_id", "code", name="uq_product_requirement_code"),
        )
        op.create_index(
            "ix_credit_product_requirements_product_id",
            "credit_product_requirements",
            ["product_id"],
        )
        op.create_index(
            "ix_credit_product_requirements_applicant_type",
            "credit_product_requirements",
            ["applicant_type"],
        )


def _create_policy_tables(bind) -> None:
    if not sa.inspect(bind).has_table("credit_policy_versions"):
        op.create_table(
            "credit_policy_versions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(60), nullable=False, unique=True),
            sa.Column("name", sa.String(140), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("effective_from", sa.Date(), nullable=False),
            sa.Column("effective_to", sa.Date()),
            sa.Column(
                "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
            ),
        )
        op.create_index("ix_credit_policy_versions_code", "credit_policy_versions", ["code"])
        op.create_index(
            "ix_credit_policy_versions_status", "credit_policy_versions", ["status"]
        )

    if not sa.inspect(bind).has_table("credit_policy_rules"):
        op.create_table(
            "credit_policy_rules",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "policy_version_id",
                sa.Integer(),
                sa.ForeignKey("credit_policy_versions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "product_id",
                sa.Integer(),
                sa.ForeignKey("credit_products.id", ondelete="CASCADE"),
            ),
            sa.Column("code", sa.String(80), nullable=False),
            sa.Column("category", sa.String(40), nullable=False),
            sa.Column("parameters", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("severity", sa.String(20), nullable=False, server_default="BLOCKING"),
            sa.Column("outcome_on_failure", sa.String(30), nullable=False),
            sa.Column("explanation", sa.Text(), nullable=False),
            sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
        op.create_index(
            "ix_credit_policy_rules_policy_version_id",
            "credit_policy_rules",
            ["policy_version_id"],
        )
        op.create_index(
            "ix_credit_policy_rules_product_id", "credit_policy_rules", ["product_id"]
        )
        op.create_index("ix_credit_policy_rules_code", "credit_policy_rules", ["code"])
        op.create_index(
            "ix_credit_policy_rules_category", "credit_policy_rules", ["category"]
        )


def _upgrade_credit_applications(bind) -> None:
    columns = _column_names(bind, "credit_applications")
    additions = (
        ("product_id", sa.Column("product_id", sa.Integer())),
        ("purpose", sa.Column("purpose", sa.String(160))),
        ("requested_payment_day", sa.Column("requested_payment_day", sa.Integer())),
        ("amortization_type", sa.Column("amortization_type", sa.String(20))),
        (
            "status",
            sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        ),
        ("updated_at", sa.Column("updated_at", sa.DateTime(timezone=True))),
    )
    pending_additions = [column for name, column in additions if name not in columns]
    if bind.dialect.name == "sqlite" and pending_additions:
        with op.batch_alter_table("credit_applications") as batch_op:
            for column in pending_additions:
                batch_op.add_column(column)
    else:
        for column in pending_additions:
            op.add_column("credit_applications", column)

    foreign_keys = sa.inspect(bind).get_foreign_keys("credit_applications")
    product_fk_exists = any(
        foreign_key.get("constrained_columns") == ["product_id"]
        and foreign_key.get("referred_table") == "credit_products"
        for foreign_key in foreign_keys
    )
    if not product_fk_exists:
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("credit_applications") as batch_op:
                batch_op.create_foreign_key(
                    "fk_credit_applications_product_id",
                    "credit_products",
                    ["product_id"],
                    ["id"],
                )
        else:
            op.create_foreign_key(
                "fk_credit_applications_product_id",
                "credit_applications",
                "credit_products",
                ["product_id"],
                ["id"],
            )
    op.create_index(
        "ix_credit_applications_product_id",
        "credit_applications",
        ["product_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_credit_applications_status",
        "credit_applications",
        ["status"],
        if_not_exists=True,
    )


def _create_operational_tables(bind) -> None:
    inspector = sa.inspect(bind)
    if not inspector.has_table("customer_financial_profiles"):
        op.create_table(
            "customer_financial_profiles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "customer_id",
                sa.Integer(),
                sa.ForeignKey("customers.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("employment_status", sa.String(30)),
            sa.Column("occupation", sa.String(120)),
            sa.Column("employer_name", sa.String(140)),
            sa.Column("economic_activity", sa.String(140)),
            sa.Column("job_tenure_months", sa.Integer()),
            sa.Column("business_tenure_months", sa.Integer()),
            sa.Column("monthly_net_income", sa.Numeric(12, 2)),
            sa.Column("other_monthly_income", sa.Numeric(12, 2)),
            sa.Column("monthly_living_expenses", sa.Numeric(12, 2)),
            sa.Column("existing_monthly_debt_payments", sa.Numeric(12, 2)),
            sa.Column("dependent_count", sa.Integer()),
            sa.Column("housing_status", sa.String(30)),
            sa.Column("assets_total", sa.Numeric(14, 2)),
            sa.Column("liabilities_total", sa.Numeric(14, 2)),
            sa.Column("source_of_funds", sa.Text()),
            sa.Column("pep_status", sa.String(20), nullable=False, server_default="UNKNOWN"),
            sa.Column(
                "identity_verification_status",
                sa.String(20),
                nullable=False,
                server_default="PENDING",
            ),
            sa.Column(
                "income_verification_status",
                sa.String(20),
                nullable=False,
                server_default="DECLARED",
            ),
            sa.Column(
                "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
            ),
            sa.Column("verified_at", sa.DateTime(timezone=True)),
        )
        op.create_index(
            "ix_customer_financial_profiles_customer_id",
            "customer_financial_profiles",
            ["customer_id"],
        )

    if not inspector.has_table("conversation_contexts"):
        op.create_table(
            "conversation_contexts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "conversation_id",
                sa.Integer(),
                sa.ForeignKey("conversations.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column(
                "active_goal",
                sa.String(50),
                nullable=False,
                server_default="CREDIT_PREQUALIFICATION",
            ),
            sa.Column("pending_field", sa.String(60)),
            sa.Column("last_intent", sa.String(50)),
            sa.Column("slots", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
            sa.Column(
                "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
            ),
            sa.Column(
                "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
            ),
        )
        op.create_index(
            "ix_conversation_contexts_conversation_id",
            "conversation_contexts",
            ["conversation_id"],
        )

    if not inspector.has_table("consent_records"):
        op.create_table(
            "consent_records",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "customer_id",
                sa.Integer(),
                sa.ForeignKey("customers.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "conversation_id",
                sa.Integer(),
                sa.ForeignKey("conversations.id", ondelete="SET NULL"),
            ),
            sa.Column("consent_type", sa.String(50), nullable=False),
            sa.Column("purpose", sa.Text(), nullable=False),
            sa.Column("notice_version", sa.String(40), nullable=False),
            sa.Column("legal_basis", sa.String(60), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("channel", sa.String(30), nullable=False, server_default="WHATSAPP"),
            sa.Column("evidence_hash", sa.String(128)),
            sa.Column("granted_at", sa.DateTime(timezone=True)),
            sa.Column("revoked_at", sa.DateTime(timezone=True)),
            sa.Column(
                "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
            ),
        )
        op.create_index("ix_consent_records_customer_id", "consent_records", ["customer_id"])
        op.create_index(
            "ix_consent_records_conversation_id", "consent_records", ["conversation_id"]
        )
        op.create_index("ix_consent_records_consent_type", "consent_records", ["consent_type"])
        op.create_index("ix_consent_records_status", "consent_records", ["status"])

    if not inspector.has_table("application_documents"):
        op.create_table(
            "application_documents",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "application_id",
                sa.Integer(),
                sa.ForeignKey("credit_applications.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("requirement_code", sa.String(60), nullable=False),
            sa.Column("document_type", sa.String(60), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
            sa.Column("source", sa.String(30), nullable=False, server_default="USER_DECLARED"),
            sa.Column("document_metadata", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column(
                "received_at", sa.DateTime(timezone=True), server_default=sa.func.now()
            ),
            sa.Column("verified_at", sa.DateTime(timezone=True)),
        )
        op.create_index(
            "ix_application_documents_application_id",
            "application_documents",
            ["application_id"],
        )
        op.create_index(
            "ix_application_documents_requirement_code",
            "application_documents",
            ["requirement_code"],
        )
        op.create_index(
            "ix_application_documents_status", "application_documents", ["status"]
        )

    if not inspector.has_table("credit_decisions"):
        op.create_table(
            "credit_decisions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "application_id",
                sa.Integer(),
                sa.ForeignKey("credit_applications.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "product_id", sa.Integer(), sa.ForeignKey("credit_products.id"), nullable=False
            ),
            sa.Column(
                "policy_version_id",
                sa.Integer(),
                sa.ForeignKey("credit_policy_versions.id"),
                nullable=False,
            ),
            sa.Column("result", sa.String(30), nullable=False),
            sa.Column("is_final_decision", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("requested_amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("proposed_term_months", sa.Integer(), nullable=False),
            sa.Column("estimated_installment", sa.Numeric(12, 2)),
            sa.Column("verified_monthly_income", sa.Numeric(12, 2)),
            sa.Column("monthly_living_expenses", sa.Numeric(12, 2)),
            sa.Column("existing_monthly_debt_payments", sa.Numeric(12, 2)),
            sa.Column("disposable_income", sa.Numeric(12, 2)),
            sa.Column("current_dti", sa.Numeric(8, 4)),
            sa.Column("projected_dti", sa.Numeric(8, 4)),
            sa.Column("credit_score", sa.Integer()),
            sa.Column("risk_level", sa.String(20)),
            sa.Column("reason_codes", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("missing_requirements", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("input_snapshot", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column(
                "calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
            ),
        )
        op.create_index(
            "ix_credit_decisions_application_id", "credit_decisions", ["application_id"]
        )
        op.create_index("ix_credit_decisions_product_id", "credit_decisions", ["product_id"])
        op.create_index(
            "ix_credit_decisions_policy_version_id",
            "credit_decisions",
            ["policy_version_id"],
        )
        op.create_index("ix_credit_decisions_result", "credit_decisions", ["result"])


def _upgrade_credit_bureau(bind) -> None:
    if bind.dialect.name != "postgresql":
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE SCHEMA IF NOT EXISTS credit_bureau")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS credit_bureau.dataset_batches (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            batch_key VARCHAR(80) NOT NULL UNIQUE,
            generator_version VARCHAR(40) NOT NULL,
            random_seed BIGINT NOT NULL,
            reference_date DATE NOT NULL,
            requested_people INTEGER NOT NULL CHECK (requested_people > 0),
            generated_people INTEGER NOT NULL DEFAULT 0 CHECK (generated_people >= 0),
            generated_accounts INTEGER NOT NULL DEFAULT 0 CHECK (generated_accounts >= 0),
            generated_payments INTEGER NOT NULL DEFAULT 0 CHECK (generated_payments >= 0),
            generated_scores INTEGER NOT NULL DEFAULT 0 CHECK (generated_scores >= 0),
            generated_inquiries INTEGER NOT NULL DEFAULT 0 CHECK (generated_inquiries >= 0),
            generated_risk_events INTEGER NOT NULL DEFAULT 0 CHECK (generated_risk_events >= 0),
            status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            validation_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMPTZ
        )
        """
    )
    people_exists = bind.execute(
        sa.text("SELECT to_regclass('credit_bureau.people') IS NOT NULL")
    ).scalar_one()
    if not people_exists:
        return

    for statement in (
        "ALTER TABLE credit_bureau.people ADD COLUMN IF NOT EXISTS dataset_batch_id UUID REFERENCES credit_bureau.dataset_batches(id) ON DELETE CASCADE",
        "ALTER TABLE credit_bureau.people ADD COLUMN IF NOT EXISTS is_synthetic BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE credit_bureau.people ADD COLUMN IF NOT EXISTS synthetic_key VARCHAR(80)",
        "ALTER TABLE credit_bureau.people ADD COLUMN IF NOT EXISTS economic_activity VARCHAR(140)",
        "ALTER TABLE credit_bureau.people ADD COLUMN IF NOT EXISTS business_tenure_months INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE credit_bureau.people ADD COLUMN IF NOT EXISTS other_monthly_income NUMERIC(12, 2) NOT NULL DEFAULT 0",
        "ALTER TABLE credit_bureau.people ADD COLUMN IF NOT EXISTS monthly_living_expenses NUMERIC(12, 2) NOT NULL DEFAULT 0",
        "ALTER TABLE credit_bureau.people ADD COLUMN IF NOT EXISTS housing_status VARCHAR(30)",
        "ALTER TABLE credit_bureau.people ADD COLUMN IF NOT EXISTS assets_total NUMERIC(14, 2) NOT NULL DEFAULT 0",
        "ALTER TABLE credit_bureau.people ADD COLUMN IF NOT EXISTS liabilities_total NUMERIC(14, 2) NOT NULL DEFAULT 0",
        "ALTER TABLE credit_bureau.people ADD COLUMN IF NOT EXISTS source_of_funds VARCHAR(160)",
        "ALTER TABLE credit_bureau.people ADD COLUMN IF NOT EXISTS identity_verified BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE credit_bureau.people ADD COLUMN IF NOT EXISTS income_verification_status VARCHAR(20) NOT NULL DEFAULT 'DECLARED'",
        "ALTER TABLE credit_bureau.people ADD COLUMN IF NOT EXISTS pep_status VARCHAR(20) NOT NULL DEFAULT 'NOT_PEP'",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_people_synthetic_key ON credit_bureau.people(synthetic_key) WHERE synthetic_key IS NOT NULL",
        "CREATE INDEX IF NOT EXISTS idx_people_dataset_batch ON credit_bureau.people(dataset_batch_id)",
    ):
        op.execute(statement)


def _column_names(bind, table_name: str) -> set[str]:
    if not sa.inspect(bind).has_table(table_name):
        return set()
    return {column["name"] for column in sa.inspect(bind).get_columns(table_name)}
