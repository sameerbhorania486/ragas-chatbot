
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

from app.core.config import CHROMA_DB_PATH, TOP_K

MAX_DISTANCE = 1.70

# New lightweight embedding model
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


@lru_cache(maxsize=1)
def get_embeddings():
    return FastEmbedEmbeddings(
        model_name=EMBEDDING_MODEL,
        max_length=512,
        threads=2,
    )


@lru_cache(maxsize=1)
def get_vector_store():
    return Chroma(
        collection_name="ragas_documents_fastembed_v1",
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

    filtered_documents = [
        document
        for document, distance in results
        if distance <= MAX_DISTANCE
    ]

    return filtered_documents
