from pydantic import BaseModel


class UserQuestionCreate(BaseModel):
    title: str
    local_user_id: str


class UserQuestionVote(BaseModel):
    local_user_id: str
