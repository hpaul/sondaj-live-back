import time
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException, Query

from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from app.api import deps
from app.models import LiveQuestion, UserQuestion
from app.core.config import settings

from app.crud.live_question import LiveQuestionCreate, LiveQuestionVote
from app.crud.user_questions import UserQuestionCreate, UserQuestionVote

from app.db.session import engine
from app.db.base_class import Base

Base.metadata.create_all(bind=engine)


root_router = APIRouter()
app = FastAPI(title="Sondaj Live API",
              openapi_url=f"/api/v1/openapi.json")

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin)
                   for origin in settings.BACKEND_CORS_ORIGINS],
    allow_origin_regex=settings.BACKEND_CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# API routes
api_router = APIRouter()

local_user_id = Query(..., min_length=1, max_length=100, alias='localUserID')

# For "/api/v1/user-question"


@api_router.get("/user-questions", status_code=200)
def user_questions(
    *,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get all active questions from the db
    """
    results = db.query(UserQuestion).filter_by(is_active=True).all()

    return results


@api_router.post("/user-questions", status_code=200)
def new_user_question(
    *,
    item: UserQuestionCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Push the new question to the database
    """
    new_question = UserQuestion(
        title=item.title,
        votes=1,
        is_active=True,
        users_voted=[item.local_user_id],
    )
    db.add(new_question)
    db.commit()

    return {"result": "success"}


@api_router.post("/user-questions/{question_id}/vote", status_code=200)
def vote_user_question(
    *,
    question_id: int,
    item: UserQuestionVote,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Push the new question to the database
    """
    question: Query[UserQuestion] = db.query(UserQuestion).filter_by(id=question_id).first()

    if item.local_user_id in question.users_voted:
        raise HTTPException(status_code=400, detail="Ai votat deja intrebarea!")

    question.users_voted.append(item.local_user_id)
    question.votes = question.votes + 1

    db.commit()

    return {"result": "success"}


@api_router.delete("/user-questions/{question_id}", status_code=200)
def delete_qustion(
    *,
    question_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Delete question from the database
    """
    db.query(UserQuestion).filter_by(id=question_id).delete()
    db.commit()
    return {"result": "success"}


# For "/api/v1/live-question"
@api_router.get("/live-question", status_code=200)
def live_question(
    *,
    local_user_id: str = local_user_id,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Fetch the current active question from the db
    """
    current_question: LiveQuestion = db.query(LiveQuestion).filter_by(is_active=True).first()

    if current_question is None:
        raise HTTPException(status_code=404, detail="Nicio intrebare nu este activa!")

    return {
        "title": current_question.title,
        "answers": current_question.answers,
        "colors": [],
        "answersVotes": [len(ids) for ids in current_question.answers_votes],
        "totalVotes": current_question.total_votes,
    }


@api_router.post("/live-question", status_code=200)
def create_live_question(
    *,
    item: LiveQuestionCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Push the new live question to the database
    """
    db.query(LiveQuestion).filter_by(is_active=True).update(
        {"is_active": False}, synchronize_session=False
    )
    live_q = LiveQuestion(
        title=item.title,
        answers=item.answers,
        answers_votes=[[]] * len(item.answers),
        total_votes=0,
        is_active=True,
    )
    db.add(live_q)
    db.commit()
    return {"result": "success"}


@api_router.post("/live-question/vote", status_code=200)
def vote_live_question(
    *,
    item: LiveQuestionVote,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Register a vote for the current live question
    """
    liveq: LiveQuestion = db.query(LiveQuestion).filter_by(is_active=True).first()

    # Check if user already voted for any of the anwers in anwers_votes
    if not any(item.local_user_id in ids for ids in liveq.answers_votes):
        liveq.total_votes += 1

    # Remove the local user id from the list of users who voted for any answer
    new_answers_votes = [
        list(filter(lambda x: x != item.local_user_id, ids))
        for ids in liveq.answers_votes
    ]

    new_answers_votes[item.index] = new_answers_votes[item.index] + [item.local_user_id]
    liveq.answers_votes = new_answers_votes

    db.commit()
    return {"result": "success"}


app.include_router(api_router, prefix="/api/v1")
app.include_router(root_router)


if __name__ == "__main__":
    # Use this for debugging purposes only
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="debug")
