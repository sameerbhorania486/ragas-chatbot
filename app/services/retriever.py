
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

from app.core.config import CHROMA_DB_PATH, TOP_K

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
    vector_store = get_vector_store()

    results = vector_store.similarity_search_with_score(
        question,
        k=TOP_K,
    )

    print("\n========== RETRIEVAL DEBUG ==========")
    print("Question:", question)
    print("Database path:", CHROMA_DB_PATH)
    print("Collection:", "ragas_documents_fastembed_v1")
    print("TOP_K:", TOP_K)
    print("Retrieved count:", len(results))

    for index, (document, distance) in enumerate(results, start=1):
        print(f"\nResult {index}")
        print("Distance:", distance)
        print("Source:", document.metadata.get("source"))
        print("Content:", document.page_content[:300])

    print("====================================\n")

    # Temporary: return all retrieved documents.
    # We will apply distance filtering after checking scores.
    return [document for document, distance in results]
