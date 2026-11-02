
from fastapi import FastAPI

from app.api.routes import router
from app.core.config import validate_config

app = FastAPI(
    title="RAGAS Chatbot API",
    description="Advanced RAG Chatbot with RAGAS Evaluation",
    version="1.0.0"
)

# Register API routes
app.include_router(
    router,
    prefix="/api/v1",
    tags=["RAG Chatbot"]
)


@app.get("/")
def home():
    return {
        "status": "success",
        "message": "RAGAS Chatbot API is running",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "application": "RAGAS Chatbot"
    }


@app.get("/requirements")
def requirements():
    return {
        "project": "RAGAS Chatbot",
        "features": [
            "Document Upload",
            "Question Answering",
            "Conversational Chat",
            "RAGAS Evaluation Results",
            "RAGAS Evaluation Reports"
        ],
        "technologies": [
            "FastAPI",
            "LangChain",
            "Groq",
            "ChromaDB",
            "HuggingFace",
            "RAGAS"
        ]
    }
