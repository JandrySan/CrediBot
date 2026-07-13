export interface Conversation {

    conversation_id: number;

    customer_id: number;

    phone_number: string;

    national_id: string | null;

    full_name: string | null;

    state: string;

    status: string;

    conversation_result: string | null;

    credit_amount: number | null;

    term_months: number | null;

    monthly_income: number | null;

    credit_result: string | null;

    credit_reason: string | null;

    created_at: string;

}
