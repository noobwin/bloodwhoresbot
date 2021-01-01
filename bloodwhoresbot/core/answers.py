from bloodwhoresbot.core.database import Database
from bloodwhoresbot.models import Context, Answer
from bloodwhoresbot.utils import get_random_file


class Answers:
    def __init__(self, db: Database):
        self._db = db
        self._answers = db.get_instance().standardAnswers

    def get(self, context: Context) -> Answer:
        answer = Answer(**get_random_file(self._answers, {"context": context.value}))
        return answer
