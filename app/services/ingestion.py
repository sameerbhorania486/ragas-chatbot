
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


# ==========================================
# 1. LOAD DOCUMENT
# ==========================================

def load_document(file_path: str):

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    extension = path.suffix.lower()

    if extension == ".pdf":
        loader = PyPDFLoader(str(path))

    elif extension == ".txt":
        loader = TextLoader(
            str(path),
            encoding="utf-8"
        )

    else:
        raise ValueError(
            "Only PDF and TXT files are supported."
        )

    documents = loader.load()

    if not documents:
        raise ValueError(
            "Document contains no readable text."
        )

    return documents


# ==========================================
# 2. SPLIT DOCUMENTS
# ==========================================

def split_documents(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            " ",
            ""
        ],
    )

    chunks = splitter.split_documents(documents)

    return chunks


# ==========================================
# 3. INGEST DOCUMENT
# ==========================================

def ingest_document(file_path: str):

    path = Path(file_path)

    # Load document
    documents = load_document(str(path))

    # Split into chunks
    chunks = split_documents(documents)

    if not chunks:
        raise ValueError(
            "No text chunks were generated."
        )

    # Generate document hash
    document_hash = hashlib.sha256(
        path.read_bytes()
    ).hexdigest()

    vector_ids = []

    # Add metadata
    for index, chunk in enumerate(chunks):

        chunk.metadata["source"] = path.name

        chunk.metadata["document_id"] = document_hash

        chunk.metadata["chunk_index"] = index

        vector_ids.append(
            f"{document_hash}_{index}"
        )

    # ======================================
    # 4. CHROMADB INDEXING
    # ======================================

    vector_store = get_vector_store()

    # DEBUG START
    print("\n========== INGESTION DEBUG ==========")

    print(
        "Database path:",
        vector_store._persist_directory
    )

    print(
        "Collection:",
        vector_store._collection.name
    )

    print(
        "Count before upload:",
        vector_store._collection.count()
    )

    print(
        "Filename:",
        path.name
    )

    print(
        "Generated chunks:",
        len(chunks)
    )

    # Delete old versions of same document
    vector_store.delete(
        ids=vector_ids
    )

    # Add new document chunks
    vector_store.add_documents(
        documents=chunks,
        ids=vector_ids
    )

    # Check actual ChromaDB count
    final_count = vector_store._collection.count()

    print(
        "Chunks submitted:",
        len(chunks)
    )

    print(
        "Count after upload:",
        final_count
    )

    print("========== INGESTION DEBUG END ==========\n")

    # ======================================
    # 5. RETURN RESULT
    # ======================================

    return {
        "filename": path.name,
        "document_id": document_hash,
        "total_pages": len(documents),
        "total_chunks": len(chunks),
        "chroma_count": final_count,
        "status": "indexed",
    }
