
from app.services.retriever import (
    get_vector_store,
    retrieve_documents,
)

# Test questions
test_questions = [
    "How many casual leaves do employees get?",
    "What are the company working hours?",
    "Who is the company CEO?",
    "When is salary credited?",
    "Which days are weekly holidays?",
]

# Load vector database
vector_store = get_vector_store()

print("=" * 60)
print("RAG RETRIEVAL THRESHOLD TEST")
print("=" * 60)

for question in test_questions:

    print("\nQuestion:", question)

    # Get raw similarity results with distances
    raw_results = vector_store.similarity_search_with_score(
        question,
        k=4,
    )

    # Get documents after threshold filtering
    filtered_results = retrieve_documents(question)

    if raw_results:
        best_distance = raw_results[0][1]
        print("Best Distance:", round(best_distance, 4))
    else:
        print("No documents found.")
        print("Status: REJECTED")
        continue

    # Display filtering result
    if filtered_results:
        print("Status: ACCEPTED")
        print("Retrieved Documents:", len(filtered_results))

        for index, document in enumerate(filtered_results, start=1):
            print(f"\nDocument {index}:")
            print(document.page_content[:200])

    else:
        print("Status: REJECTED")
        print("No relevant document found.")

    print("\n" + "-" * 60)

print("\nRetrieval testing completed.")
