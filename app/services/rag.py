
from langchain_core.prompts import ChatPromptTemplate

from app.services.llm import get_llm
from app.services.retriever import retrieve_documents


RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
You are a helpful document-based AI assistant.

Answer the user's question using ONLY the information
available in the provided context.

Rules:
1. Do not invent facts.
2. If the answer is not available in the context,
   clearly say that the uploaded documents do not contain it.
3. Give clear and simple answers.
4. Use conversation history to understand follow-up questions,
   but never use it as factual evidence.

Context:
{context}

Conversation History:
{chat_history}
"""),
    ("human", "{question}")
])


def format_documents(documents):
    return "\n\n".join(
        [
            f"Source: {doc.metadata.get('source', 'Unknown')}\n"
            f"Content: {doc.page_content}"
            for doc in documents
        ]
    )


def build_retrieval_query(question: str, chat_history: str = ""):
    """
    Add the previous user question to a follow-up query
    to provide additional context for document retrieval.
    """

    if not chat_history.strip():
        return question

    previous_user_questions = []

    for line in chat_history.splitlines():
        if line.lower().startswith("user:"):
            previous_user_questions.append(
                line.split(":", 1)[1].strip()
            )

    if not previous_user_questions:
        return question

    previous_question = previous_user_questions[-1]

    return (
        f"Previous question: {previous_question}\n"
        f"Current question: {question}"
    )


def generate_answer(question: str, chat_history: str = ""):

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    retrieval_query = build_retrieval_query(
        question,
        chat_history
    )

    documents = retrieve_documents(retrieval_query)

    if not documents:
        return {
            "answer": "I could not find relevant information in the uploaded documents.",
            "sources": [],
            "retrieved_contexts": [],
        }

    context = format_documents(documents)

    prompt = RAG_PROMPT.invoke({
        "context": context,
        "question": question,
        "chat_history": chat_history,
    })

    response = get_llm().invoke(prompt)

    sources = []

    for document in documents:
        sources.append({
            "filename": document.metadata.get("source", "Unknown"),
            "page": document.metadata.get("page"),
            "chunk_index": document.metadata.get("chunk_index"),
            "content_preview": document.page_content[:250],
        })

    return {
        "answer": response.content,
        "sources": sources,
        "retrieved_contexts": [
            document.page_content for document in documents
        ],
    }
