
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import FileResponse

from app.core.config import DOCUMENTS_PATH, REPORTS_PATH
from app.schemas.models import QuestionRequest, ChatRequest

from app.services.ingestion import ingest_document
from app.services.rag import generate_answer

from app.services.evaluator import (
    run_evaluation,
    load_saved_evaluation,
)

from app.services.report_generator import generate_reports

from app.services.chat_memory import (
    initialize_chat_database,
    save_message,
    get_chat_history,
    get_session_messages,
    get_all_sessions,
    delete_chat_session,
    rename_chat_session,
    search_chat_history,
    clear_chat_history,
)


router = APIRouter()


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

initialize_chat_database()


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

MAX_FILE_SIZE = 20 * 1024 * 1024

ALLOWED_EXTENSIONS = {".pdf", ".txt"}

ALLOWED_REPORT_EXTENSIONS = {".json", ".csv", ".pdf"}


# --------------------------------------------------
# 1. DOCUMENT UPLOAD API
# --------------------------------------------------

@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):

    filename = Path(file.filename or "").name

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required."
        )

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported."
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Maximum file size is 20 MB."
        )

    destination = DOCUMENTS_PATH / filename

    try:
        destination.write_bytes(content)

        result = ingest_document(str(destination))

        return {
            "status": "success",
            "message": "Document uploaded and indexed successfully.",
            "data": result
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Document ingestion failed: {str(error)}"
        )

    finally:
        await file.close()


# --------------------------------------------------
# 2. LIST DOCUMENTS API
# --------------------------------------------------

@router.get("/documents")
def list_documents():

    files = [
        {
            "filename": file.name,
            "size_bytes": file.stat().st_size
        }
        for file in DOCUMENTS_PATH.iterdir()
        if file.is_file()
        and file.suffix.lower() in ALLOWED_EXTENSIONS
    ]

    return {
        "total_documents": len(files),
        "documents": files
    }


# --------------------------------------------------
# 3. QUESTION ANSWERING API
# --------------------------------------------------

@router.post("/qa")
def question_answering(request: QuestionRequest):

    try:
        result = generate_answer(
            question=request.question
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Question answering failed: {str(error)}"
        )


# --------------------------------------------------
# 4. CONVERSATIONAL CHAT API
# --------------------------------------------------

@router.post("/chat")
def conversational_chat(request: ChatRequest):

    session_id = request.session_id or str(uuid4())

    try:
        # Load previous messages
        history = get_chat_history(
            session_id=session_id,
            limit=10
        )

        # Convert history into text
        chat_history = "\n".join(
            [
                f"{message['role']}: {message['content']}"
                for message in history
            ]
        )

        # Generate RAG answer
        result = generate_answer(
            question=request.question,
            chat_history=chat_history
        )

        # Save user message
        save_message(
            session_id=session_id,
            role="user",
            content=request.question
        )

        # Save assistant response
        save_message(
            session_id=session_id,
            role="assistant",
            content=result["answer"]
        )

        return {
            "session_id": session_id,
            **result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(error)}"
        )


# --------------------------------------------------
# 5. GET COMPLETE CHAT HISTORY API
# --------------------------------------------------

@router.get("/chat/{session_id}/history")
def get_conversation_history(session_id: str):

    try:
        messages = get_session_messages(session_id)

        return {
            "session_id": session_id,
            "total_messages": len(messages),
            "messages": messages
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve chat history: {str(error)}"
        )


# --------------------------------------------------
# 6. LIST ALL CHAT SESSIONS API
# --------------------------------------------------

@router.get("/chat/sessions")
def list_chat_sessions():

    try:
        sessions = get_all_sessions()

        return {
            "total_sessions": len(sessions),
            "sessions": sessions
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve chat sessions: {str(error)}"
        )


# --------------------------------------------------
# 7. DELETE COMPLETE CHAT SESSION API
# --------------------------------------------------

@router.delete("/chat/{session_id}")
def remove_chat_session(session_id: str):

    try:
        deleted_messages = delete_chat_session(session_id)

        if deleted_messages == 0:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found."
            )

        return {
            "status": "success",
            "message": "Chat session deleted successfully.",
            "session_id": session_id,
            "deleted_messages": deleted_messages
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not delete chat session: {str(error)}"
        )


# --------------------------------------------------
# 8. RENAME CHAT SESSION API
# --------------------------------------------------

@router.patch("/chat/{session_id}/rename")
def rename_session(
    session_id: str,
    new_title: str = Body(..., embed=True)
):

    try:
        updated = rename_chat_session(
            session_id=session_id,
            new_title=new_title
        )

        if updated == 0:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found."
            )

        return {
            "status": "success",
            "message": "Chat session renamed successfully.",
            "session_id": session_id,
            "new_title": new_title.strip()
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not rename chat session: {str(error)}"
        )


# --------------------------------------------------
# 9. SEARCH CHAT HISTORY API
# --------------------------------------------------

@router.get("/chat/search")
def search_chats(query: str):

    try:
        results = search_chat_history(query)

        return {
            "status": "success",
            "query": query,
            "total_results": len(results),
            "results": results
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Chat search failed: {str(error)}"
        )


# --------------------------------------------------
# 10. CLEAR CHAT HISTORY API
# --------------------------------------------------

@router.delete("/chat/{session_id}/history")
def clear_session_history(session_id: str):

    try:
        messages = get_session_messages(session_id)

        if not messages:
            raise HTTPException(
                status_code=404,
                detail="No chat messages found for this session."
            )

        deleted_messages = clear_chat_history(session_id)

        return {
            "status": "success",
            "message": "Chat history cleared successfully.",
            "session_id": session_id,
            "deleted_messages": deleted_messages
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not clear chat history: {str(error)}"
        )


# --------------------------------------------------
# 11. RAGAS EVALUATION API
# --------------------------------------------------

@router.post("/evaluation/run")
def evaluate_chatbot():

    try:
        result = run_evaluation()

        return {
            "status": "success",
            "message": "RAGAS evaluation completed successfully.",
            "evaluation": result
        }

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(error)}"
        )


# --------------------------------------------------
# 12. GENERATE REPORTS FROM SAVED EVALUATION
# --------------------------------------------------

@router.post("/evaluation/reports/generate")
def generate_saved_reports():

    try:
        evaluation = load_saved_evaluation()

        reports = generate_reports(evaluation)

        return {
            "status": "success",
            "message": "Reports generated from saved evaluation.",
            "reports": reports
        }

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(error)}"
        )


# --------------------------------------------------
# 13. REPORT DOWNLOAD API
# --------------------------------------------------

@router.get("/reports/{filename}")
def download_report(filename: str):

    safe_name = Path(filename).name

    if safe_name != filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename."
        )

    if not safe_name.startswith("evaluation_"):
        raise HTTPException(
            status_code=400,
            detail="Invalid report filename."
        )

    if Path(safe_name).suffix.lower() not in ALLOWED_REPORT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported report format."
        )

    report_path = REPORTS_PATH / safe_name

    if not report_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Report not found."
        )

    return FileResponse(
        path=str(report_path),
        filename=safe_name
    )
