from typing import List
from pydantic import BaseModel


class LiveQuestionCreate(BaseModel):
    title: str
    answers: List[str]


class LiveQuestionVote(BaseModel):
    index: int
    local_user_id: str
