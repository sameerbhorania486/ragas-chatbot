
import os
from pathlib import Path
from dotenv import load_dotenv

# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Load .env
load_dotenv(BASE_DIR / ".env")

# API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)

# Embedding configuration
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
)

# Database configuration
CHROMA_DB_PATH = BASE_DIR / "chroma_db"


# Document configuration
DOCUMENTS_PATH = BASE_DIR / os.getenv(
    "DOCUMENTS_PATH", "./data/documents"
)

# Evaluation and report configuration
EVALUATION_PATH = BASE_DIR / "data" / "evaluation"
REPORTS_PATH = BASE_DIR / os.getenv(
    "REPORTS_PATH", "./reports"
)

# RAG configuration
TOP_K = int(os.getenv("TOP_K", "4"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# Create required directories
for directory in [
    CHROMA_DB_PATH,
    DOCUMENTS_PATH,
    EVALUATION_PATH,
    REPORTS_PATH
]:
    directory.mkdir(parents=True, exist_ok=True)


def validate_config():
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY missing. Please configure your .env file."
        )
