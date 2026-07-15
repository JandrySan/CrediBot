from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.services.rag.faq_loader import FAQLoader
from app.services.rag.models import KnowledgeBase
from app.services.rag.retrieval_service import RetrievalService


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=_DisposableSession,
    )
    return testing_session()


class _DisposableSession(Session):
    def close(self) -> None:
        bind = self.get_bind()
        super().close()
        bind.dispose()


def test_faq_loader_loads_json_rows_and_keywords():
    db = _session()
    try:
        result = FAQLoader(db).load_json(
            """
            [
              {
                "question": "Cuales son los requisitos?",
                "answer": "Documento de identidad e ingresos comprobables.",
                "category": "requisitos",
                "keywords": ["requisitos", "documentos"]
              }
            ]
            """
        )

        assert result["created"] == 1
        faq = db.query(KnowledgeBase).first()
        assert faq is not None
        assert faq.category == "requisitos"
        assert "documentos" in faq.keyword_list()
    finally:
        db.close()


def test_retrieval_service_returns_best_keyword_match():
    db = _session()
    try:
        faq = KnowledgeBase(
            question="Que documentos necesito?",
            answer="Necesitas cedula y comprobante de ingresos.",
            category="requisitos",
        )
        faq.set_keywords(["documentos", "cedula", "ingresos"])
        db.add(faq)
        db.commit()

        match = RetrievalService(db).best_match("necesito documentos para credito")

        assert match is not None
        assert match.answer == "Necesitas cedula y comprobante de ingresos."
    finally:
        db.close()
