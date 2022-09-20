from typing import List
from sqlalchemy import Integer, String, Column, Boolean, PickleType
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class LiveQuestion(Base):
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=True)
    answers = Column(PickleType(), nullable=True)
    answers_votes = Column(PickleType(), nullable=True)
    total_votes = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=True)
    # Keep track of the user who voted on the question
    users_voted = Column(PickleType(), nullable=True)
