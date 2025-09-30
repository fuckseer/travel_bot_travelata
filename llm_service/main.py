from fastapi import FastAPI

app = FastAPI()

@app.post("/parse")
def parse_request(query: dict):
    return {"msg": "LLM service is alive", "query": query}