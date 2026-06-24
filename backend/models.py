from sqlalchemy import Column, Integer, String, Index
from database import Base

class DrugInteraction(Base):
    
    __tablename = "drug_interactions"

    id = Column(Integer, primary_key=True, index=True)

    drug_a = Column(String, nullable=False)

    drug_b = Column(String, nullable=False)

    __table_args__ = (
        Index("ix_drug_pair", "drug_a", "drug_b"),
    )