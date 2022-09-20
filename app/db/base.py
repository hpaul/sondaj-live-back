# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base  # noqa
from app.models.live_question import LiveQuestion  # noqa
from app.models.user_question import UserQuestion  # noqa
