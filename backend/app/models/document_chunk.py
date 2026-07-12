from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.database.base import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(String, nullable=True)
    source_info = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
