from fastapi import FastAPI, status, WebSocket
from pydantic import BaseModel
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4, UUID


app = FastAPI()


class Session:
    def __init__(self) -> None:
        self.questioner: Optional[WebSocket]
        self.participants: Dict[str, WebSocket] = {}
        self.answers: List[Tuple[str, str, int, int]] = []

    async def broadcast(self, data: Any):
        for ws in self.participants.values():
            await ws.send_json(data)

    async def join_as(self, name: str, role: Literal["questioner", "participant"], ws: WebSocket):
        if role == "questioner":
            self.questioner = ws
        self.participants[name] = ws
        await ws.send_json({"type": "answers", "answers": self.answers})

    async def answer(self, name: str, answer: str, hits: int, blows: int):
        if name in self.participants:
            ws = self.participants[name]
            self.answers.append((name, answer, hits, blows))
            await ws.send_json(
                {
                    "type": "result",
                    "hits": hits,
                    "blows": blows,
                    "result": "Win" if hits == 4 else "Fail",
                }
            )

            await self.broadcast({"type": "answers", "answers": self.answers})


sessions: Dict[UUID, Session] = {}


class Game(BaseModel):
    id: Optional[UUID]
    title: str
    question: str

    def result(self, answer: str) -> Tuple[int, int]:
        hits = sum(a == b for a, b in zip(self.question, answer))
        blows = sum(a == b for a in self.question for b in answer) - hits
        return hits, blows


class QuestionRegistry(BaseModel):
    list: List[Game] = []

    def all(self) -> Tuple[Game, ...]:
        return tuple(self.list)

    def get_by_id(self, id: UUID) -> Optional[Game]:
        g = filter(lambda g: g.id == id, self.list)
        return next(g, None)

    def register(self, game: Game):
        g = Game(id=uuid4(), question=game.question, title=game.title)
        self.list.append(g)
        return g.id

    def delete_by_id(self, id: UUID) -> None:
        g = self.get_by_id(id)
        if g is not None:
            self.list.remove(g)


registry = QuestionRegistry()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/games", status_code=status.HTTP_201_CREATED)
def register_game(game: Game):
    id = registry.register(game)
    if id is not None:
        sessions[id] = Session()
        return {"id": id}


@app.delete("/games/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_game_by_id(game_id: UUID):
    registry.delete_by_id(game_id)


@app.websocket("/games/{game_id}/ws")
async def websocket_endpoint(game_id: UUID, ws: WebSocket):
    game = registry.get_by_id(game_id)
    if game is None:
        await ws.close()
    else:
        session = sessions[game_id]

        await ws.accept()
        name: Optional[str] = None
        while True:
            data = await ws.receive_json()
            command = data["command"]
            payload = data["payload"]

            if command == "join":
                if (
                    "name" in payload
                    and type(payload["name"]) is str
                    and "role" in payload
                    and payload["role"] in ["questioner", "participant"]
                ):
                    name = payload["name"]
                    role = payload["role"]
                    await session.join_as(payload["name"], role, ws)
            elif command == "answer":
                if "answer" in payload and type(payload["answer"]) is str and name is not None:
                    answer: str = payload["answer"]
                    hits, blows = game.result(answer)
                    await session.answer(name, answer, hits, blows)
                    await ws.send_json({"message": f"Hello {name}!"})
                else:
                    await ws.send_json({"message": "name is reqired."})
                await ws.send_json({})


@app.get("/questions")
def get_questions():
    return list(map(lambda g: {"id": g.id, "title": g.title}, registry.all()))
    # return registry.all()
