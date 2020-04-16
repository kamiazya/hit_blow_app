from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Tuple
from uuid import uuid4, UUID


app = FastAPI()


class User(BaseModel):
    name: str


class Question(BaseModel):
    id: Optional[UUID]
    title: str
    question: Tuple[int, int, int, int]


class QuestionRegistry(BaseModel):
    list: List[Question] = []

    def all(self) -> Tuple[Question, ...]:
        return tuple(self.list)

    def get_by_id(self, id: UUID) -> Optional[Question]:
        q = filter(lambda q: q.id == id, self.list)
        return next(q, None)

    def register(self, question: Question):
        q = Question(id=uuid4(), question=question.question, title=question.title)
        self.list.append(q)
        return q.id

    def delete_by_id(self, id: UUID) -> None:
        q = self.get_by_id(id)
        if q is not None:
            self.list.remove(q)


registry = QuestionRegistry()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/questions")
def register_question(question: Question):
    id = registry.register(question)
    return {"id": id}


@app.delete("/questions/{question_id}")
def delete_question_by_id(question_id: UUID):
    registry.delete_by_id(question_id)


@app.get("/questions")
def get_questions():
    return registry.all()
