from fastapi import FastAPI
from pydantic import BaseModel
from llm_service.llm_client import parse_user_request  # теперь пакет виден

app = FastAPI()

class Query(BaseModel):
    query: str

@app.post("/parse")
def parse_request(q: Query):
    parsed = parse_user_request(q.query)
    return parsed