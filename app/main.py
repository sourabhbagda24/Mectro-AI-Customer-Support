import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from app.orchestrator import run_support_pipeline

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Mectro AI Customer Support System",
    description=(
        "Multi-agent AI customer support system built with LangChain Agents "
        "(Intent Detection -> MySQL Database Agent -> Response Generator), "
        "served over FastAPI and powered by Groq."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"))


class SupportQueryRequest(BaseModel):
    customer_query: str = Field(..., min_length=1, example="I would like to know your refund policy.")


class SupportQueryResponse(BaseModel):
    customer_query: str
    detected_intent: str
    intent_reasoning: str
    order_id: str | None
    retrieved_data: str
    final_response: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/support/query", response_model=SupportQueryResponse)
def support_query(request: SupportQueryRequest):
    try:
        result = run_support_pipeline(request.customer_query)
        return result
    except Exception as e:
        logging.exception("Pipeline failed")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
