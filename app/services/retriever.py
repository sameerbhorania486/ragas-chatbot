
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import (
    CHROMA_DB_PATH,
    EMBEDDING_MODEL,
    TOP_K,
)

# Similarity threshold
# Lower distance means more similar in Chroma distance search.
MAX_DISTANCE = 1.70


@lru_cache(maxsize=1)
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


@lru_cache(maxsize=1)
def get_vector_store():
    return Chroma(
        collection_name="ragas_documents",
        embedding_function=get_embeddings(),
        persist_directory=str(CHROMA_DB_PATH),
    )


def get_retriever():
    return get_vector_store().as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K},
    )


def retrieve_documents(question: str):
    results = get_vector_store().similarity_search_with_score(
        question,
        k=TOP_K,
    )

    # Keep only documents within the distance threshold
    filtered_documents = [
        document
        for document, distance in results
        if distance <= MAX_DISTANCE
    ]

    return filtered_documents
