"""Versiona el esquema operativo público existente."""

from alembic import op
import sqlalchemy as sa


revision = "20260715_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    _create_customers(bind)
    _create_conversations(bind)
    _create_messages(bind)
    _create_credit_applications(bind)
    _create_ai_analysis(bind)
    _create_state_history(bind)
    _create_knowledge_base(bind)
    _upgrade_existing_columns(bind)


def downgrade() -> None:
    for table in (
        "knowledge_base",
        "conversation_state_history",
        "ai_analysis",
        "messages",
        "credit_applications",
        "conversations",
        "customers",
    ):
        if sa.inspect(op.get_bind()).has_table(table):
            op.drop_table(table)


def _create_customers(bind) -> None:
    if sa.inspect(bind).has_table("customers"):
        return
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("phone_number", sa.String(30), nullable=False, unique=True),
        sa.Column("national_id", sa.String(10)),
        sa.Column("full_name", sa.String(120)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_customers_phone_number", "customers", ["phone_number"])
    op.create_index("ix_customers_national_id", "customers", ["national_id"])


def _create_conversations(bind) -> None:
    if sa.inspect(bind).has_table("conversations"):
        return
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("current_state", sa.String(50), nullable=False, server_default="START"),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("result", sa.String(50)),
        sa.Column("response_mode", sa.String(20), nullable=False, server_default="TEXT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )


def _create_messages(bind) -> None:
    if sa.inspect(bind).has_table("messages"):
        return
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("message_type", sa.String(20), nullable=False, server_default="TEXT"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def _create_credit_applications(bind) -> None:
    if sa.inspect(bind).has_table("credit_applications"):
        return
    op.create_table(
        "credit_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("credit_type", sa.String(50)),
        sa.Column("amount", sa.Numeric(12, 2)),
        sa.Column("term_months", sa.Integer()),
        sa.Column("monthly_income", sa.Numeric(12, 2)),
        sa.Column("result", sa.String(50)),
        sa.Column("reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def _create_ai_analysis(bind) -> None:
    if sa.inspect(bind).has_table("ai_analysis"):
        return
    op.create_table(
        "ai_analysis",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("intent", sa.String(50)),
        sa.Column("extracted_data", sa.Text()),
        sa.Column("model_used", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def _create_state_history(bind) -> None:
    if sa.inspect(bind).has_table("conversation_state_history"):
        return
    op.create_table(
        "conversation_state_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("previous_state", sa.String(50)),
        sa.Column("new_state", sa.String(50), nullable=False),
        sa.Column("reason", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def _create_knowledge_base(bind) -> None:
    if sa.inspect(bind).has_table("knowledge_base"):
        return
    op.create_table(
        "knowledge_base",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("category", sa.String(80)),
        sa.Column("keywords", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_knowledge_base_category", "knowledge_base", ["category"])
    op.create_index("ix_knowledge_base_is_active", "knowledge_base", ["is_active"])


def _upgrade_existing_columns(bind) -> None:
    inspector = sa.inspect(bind)
    customer_columns = {column["name"] for column in inspector.get_columns("customers")}
    if "national_id" not in customer_columns:
        op.add_column("customers", sa.Column("national_id", sa.String(10)))

    conversation_columns = {
        column["name"] for column in inspector.get_columns("conversations")
    }
    if "response_mode" not in conversation_columns:
        op.add_column(
            "conversations",
            sa.Column("response_mode", sa.String(20), nullable=False, server_default="TEXT"),
        )

    if bind.dialect.name != "sqlite":
        application_columns = {
            column["name"]: column
            for column in inspector.get_columns("credit_applications")
        }
        reason = application_columns.get("reason")
        if reason and "TEXT" not in str(reason["type"]).upper():
            op.alter_column("credit_applications", "reason", type_=sa.Text())
