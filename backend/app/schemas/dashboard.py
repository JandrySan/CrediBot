from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DashboardStats(BaseModel):
    customers: int
    conversations: int
    active_conversations: int
    handoff_conversations: int
    closed_conversations: int
    preapproved: int
    observed: int


class ConversationSummary(BaseModel):
    conversation_id: int
    customer_id: int
    phone_number: str
    national_id: str | None
    full_name: str | None
    state: str
    status: str
    conversation_result: str | None
    credit_amount: float | None
    term_months: int | None
    monthly_income: float | None
    credit_result: str | None
    credit_reason: str | None
    created_at: datetime


class ConversationMessage(BaseModel):
    id: int
    direction: str
    type: str
    content: str
    created_at: datetime


class ActionResponse(BaseModel):
    success: bool
    message: str
    conversation_id: int | None = None
    status: str | None = None
    state: str | None = None
    resolution: str | None = None
    customer_notified: bool | None = None
    message_saved: bool | None = None
    whatsapp_sent: bool | None = None
    twilio: dict[str, Any] | None = None


class CleanupResponse(BaseModel):
    success: bool = True
    closed_count: int
    deleted_count: int


class FAQItem(BaseModel):
    id: int
    question: str
    answer: str
    category: str | None
    keywords: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


class FAQUploadResponse(BaseModel):
    success: bool
    message: str
    created: int = 0
    skipped: int = 0
    errors: list[dict[str, Any]] = Field(default_factory=list)


class FAQDeleteResponse(BaseModel):
    success: bool
    message: str
    faq_id: int | None = None
