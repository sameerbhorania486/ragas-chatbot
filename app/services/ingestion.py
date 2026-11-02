
import hashlib
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from app.services.retriever import get_vector_store


def load_document(file_path: str):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    extension = path.suffix.lower()

    if extension == ".pdf":
        loader = PyPDFLoader(str(path))
    elif extension == ".txt":
        loader = TextLoader(str(path), encoding="utf-8")
    else:
        raise ValueError("Only PDF and TXT files are supported.")

    documents = loader.load()

    if not documents:
        raise ValueError("Document contains no readable text.")

    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )

    return splitter.split_documents(documents)


def ingest_document(file_path: str):
    path = Path(file_path)

    documents = load_document(str(path))
    chunks = split_documents(documents)

    if not chunks:
        raise ValueError("No text chunks were generated.")

    document_hash = hashlib.sha256(
        path.read_bytes()
    ).hexdigest()

    vector_ids = []

    for index, chunk in enumerate(chunks):
        chunk.metadata["source"] = path.name
        chunk.metadata["document_id"] = document_hash
        chunk.metadata["chunk_index"] = index

        vector_ids.append(f"{document_hash}_{index}")

    vector_store = get_vector_store()

    # Avoid duplicate chunks when the same document is uploaded again.
    vector_store.delete(ids=vector_ids)

    vector_store.add_documents(
        documents=chunks,
        ids=vector_ids,
    )

    return {
        "filename": path.name,
        "document_id": document_hash,
        "total_pages": len(documents),
        "total_chunks": len(chunks),
        "status": "indexed",
    }
