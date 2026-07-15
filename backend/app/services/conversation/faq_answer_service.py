from sqlalchemy.orm import Session

from app.services.conversation.policy import ConversationPolicy
from app.services.rag.retrieval_service import RetrievalService


class FAQAnswerService:
    def __init__(self, db: Session, response_generator):
        self.retrieval = RetrievalService(db)
        self.response_generator = response_generator

    def answer(self, text: str) -> str:
        if not ConversationPolicy.is_faq_question(text):
            return ""

        faq = self.retrieval.best_match(text)
        if not faq:
            return ""

        base_response = (
            f"{faq.answer} Si quieres, tambien puedo ayudarte con tu precalificacion de credito."
        )
        return self.response_generator.generate(
            base_message=base_response,
            last_user_message=text,
            faq_context=f"Pregunta: {faq.question}\nRespuesta: {faq.answer}",
        )
