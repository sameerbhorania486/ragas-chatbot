
import os
import requests
import streamlit as st
from pathlib import Path


# =====================================================
# CONFIGURATION
# =====================================================

DEFAULT_BACKEND_URL = "https://ragas-chatbot.onrender.com"

try:
    BACKEND_URL = st.secrets.get(
        "BACKEND_URL",
        os.getenv("BACKEND_URL", DEFAULT_BACKEND_URL),
    )
except Exception:
    BACKEND_URL = os.getenv(
        "BACKEND_URL",
        DEFAULT_BACKEND_URL,
    )

BACKEND_URL = BACKEND_URL.rstrip("/")
API_BASE_URL = f"{BACKEND_URL}/api/v1"

REQUEST_TIMEOUT = 180


st.set_page_config(
    page_title="RAGAS AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =====================================================
# SESSION STATE
# =====================================================

defaults = {
    "session_id": None,
    "messages": [],
    "evaluation_result": None,
    "generated_reports": {},
    "refresh_documents": False,
    "debug_response": None,
    "debug_question": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================================================
# API ERROR HANDLER
# =====================================================

def show_api_error(response, label="API Error"):

    st.error(label)

    try:
        st.json(response.json())

    except Exception:
        st.code(response.text)


# =====================================================
# API GET
# =====================================================

def api_get(endpoint, params=None):

    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:
        st.error("Backend request timed out.")

    except requests.exceptions.HTTPError:
        show_api_error(
            response,
            "HTTP error while calling backend.",
        )

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to backend server.")

    except requests.exceptions.RequestException as error:
        st.error(f"API Error: {error}")

    except ValueError:
        st.error("Backend returned invalid JSON.")
        st.code(response.text)

    return None


# =====================================================
# API POST
# =====================================================

def api_post(endpoint, payload=None):

    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:
        st.error("Backend request timed out.")

    except requests.exceptions.HTTPError:
        show_api_error(
            response,
            "HTTP error while calling backend.",
        )

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to backend server.")

    except requests.exceptions.RequestException as error:
        st.error(f"API Error: {error}")

    except ValueError:
        st.error("Backend returned invalid JSON.")
        st.code(response.text)

    return None


# =====================================================
# API PATCH
# =====================================================

def api_patch(endpoint, payload):

    try:
        response = requests.patch(
            f"{API_BASE_URL}{endpoint}",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:
        st.error("Backend request timed out.")

    except requests.exceptions.HTTPError:
        show_api_error(
            response,
            "HTTP error while calling backend.",
        )

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to backend server.")

    except requests.exceptions.RequestException as error:
        st.error(f"API Error: {error}")

    except ValueError:
        st.error("Backend returned invalid JSON.")
        st.code(response.text)

    return None


# =====================================================
# API DELETE
# =====================================================

def api_delete(endpoint):

    try:
        response = requests.delete(
            f"{API_BASE_URL}{endpoint}",
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:
        st.error("Backend request timed out.")

    except requests.exceptions.HTTPError:
        show_api_error(
            response,
            "HTTP error while calling backend.",
        )

    except requests.exceptions.ConnectionError:
        st.error("Could not connect to backend server.")

    except requests.exceptions.RequestException as error:
        st.error(f"API Error: {error}")

    except ValueError:
        st.error("Backend returned invalid JSON.")
        st.code(response.text)

    return None


# =====================================================
# CHAT FUNCTIONS
# =====================================================

def new_chat():

    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.debug_response = None
    st.session_state.debug_question = None


def load_chat(session_id):

    result = api_get(
        f"/chat/{session_id}/history"
    )

    if result is not None:

        st.session_state.session_id = session_id

        st.session_state.messages = result.get(
            "messages",
            [],
        )

        st.session_state.debug_response = None
        st.session_state.debug_question = None


# =====================================================
# SEND MESSAGE
# =====================================================

def send_message(question):

    payload = {
        "question": question,
    }

    if st.session_state.session_id:

        payload["session_id"] = (
            st.session_state.session_id
        )

    # Save question for debugging
    st.session_state.debug_question = question

    # Call backend API
    result = api_post(
        "/chat",
        payload,
    )

    # SAVE RAW BACKEND RESPONSE
    # This survives st.rerun()

    st.session_state.debug_response = result

    if not result:

        return

    # Session ID
    st.session_state.session_id = result.get(
        "session_id",
        st.session_state.session_id,
    )

    # Answer
    answer = result.get(
        "answer",
        result.get(
            "response",
            "No answer received from backend.",
        ),
    )

    # Sources
    sources = result.get(
        "sources",
        [],
    )

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": question,
    })

    # Save assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })


# =====================================================
# SOURCE DISPLAY
# =====================================================

def display_sources(sources):

    if not sources:
        return

    with st.expander("📚 View Sources"):

        for index, source in enumerate(
            sources,
            start=1,
        ):

            st.markdown(
                f"**Source {index}**"
            )

            if isinstance(source, dict):

                st.json(source)

            else:

                st.write(source)


# =====================================================
# DOCUMENT UPLOAD
# =====================================================

def upload_document(uploaded_file):

    try:

        response = requests.post(
            f"{API_BASE_URL}/documents/upload",

            files={
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type
                    or "application/octet-stream",
                )
            },

            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:

        st.error("Document upload timed out.")

    except requests.exceptions.HTTPError:

        show_api_error(
            response,
            "Document upload failed.",
        )

    except requests.exceptions.ConnectionError:

        st.error("Could not connect to backend.")

    except requests.exceptions.RequestException as error:

        st.error(
            f"Document upload failed: {error}"
        )

    except ValueError:

        st.error("Backend returned invalid JSON.")
        st.code(response.text)

    return None


# =====================================================
# REPORT DOWNLOAD
# =====================================================

def download_report(filename):

    try:

        response = requests.get(
            f"{API_BASE_URL}/reports/{filename}",
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.content

    except requests.exceptions.Timeout:

        st.error("Report download timed out.")

    except requests.exceptions.HTTPError:

        show_api_error(
            response,
            "Report download failed.",
        )

    except requests.exceptions.ConnectionError:

        st.error("Could not connect to backend.")

    except requests.exceptions.RequestException as error:

        st.error(
            f"Report download failed: {error}"
        )

    return None


# =====================================================
# FIND REPORT FILENAMES
# =====================================================

def find_report_filenames(data):

    found = []

    def scan(value):

        if isinstance(value, dict):

            for item in value.values():
                scan(item)

        elif isinstance(value, list):

            for item in value:
                scan(item)

        elif isinstance(value, str):

            name = Path(value).name

            if (
                name.startswith("evaluation_")
                and Path(name).suffix.lower()
                in {".json", ".csv", ".pdf"}
                and name not in found
            ):

                found.append(name)

    scan(data)

    return found


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.title("🤖 RAGAS AI")

    st.caption(
        "Retrieval Augmented Generation Assistant"
    )

    st.divider()

    # NEW CHAT

    if st.button(
        "➕ New Chat",
        use_container_width=True,
    ):

        new_chat()

        st.rerun()

    st.divider()

    # CHAT HISTORY

    st.subheader("💬 Chat History")

    sessions_data = api_get(
        "/chat/sessions"
    )

    sessions = (
        sessions_data.get("sessions", [])
        if sessions_data
        else []
    )

    for session in sessions:

        session_id = session.get(
            "session_id"
        )

        if not session_id:
            continue

        title = session.get(
            "title",
            "New Chat",
        )

        with st.expander(f"💬 {title}"):

            # OPEN CHAT

            if st.button(
                "Open Chat",
                key=f"open_{session_id}",
                use_container_width=True,
            ):

                load_chat(session_id)

                st.rerun()

            # RENAME CHAT

            new_title = st.text_input(
                "Chat title",
                value=title,
                key=f"title_{session_id}",
            )

            if st.button(
                "Rename",
                key=f"rename_{session_id}",
                use_container_width=True,
            ):

                result = api_patch(
                    f"/chat/{session_id}/rename",
                    {
                        "new_title": new_title
                    },
                )

                if result:

                    st.success(
                        "Chat renamed successfully!"
                    )

                    st.rerun()

            # DELETE CHAT

            if st.button(
                "Delete Chat",
                key=f"delete_{session_id}",
                use_container_width=True,
            ):

                result = api_delete(
                    f"/chat/{session_id}"
                )

                if result:

                    if (
                        st.session_state.session_id
                        == session_id
                    ):

                        new_chat()

                    st.success("Chat deleted!")

                    st.rerun()

    # SEARCH CHAT

    st.divider()

    st.subheader("🔎 Search Chats")

    search_query = st.text_input(
        "Search previous messages",
        key="search_query",
    )

    if st.button(
        "Search",
        use_container_width=True,
    ):

        if search_query.strip():

            search_result = api_get(
                "/chat/search",
                params={
                    "query": search_query
                },
            )

            if search_result:

                st.write(
                    "Results: "
                    + str(
                        search_result.get(
                            "total_results",
                            0,
                        )
                    )
                )

                for item in search_result.get(
                    "results",
                    [],
                ):

                    st.write(item)

        else:

            st.warning(
                "Enter a search keyword."
            )

    # DOCUMENT MANAGEMENT

    st.divider()

    st.subheader("📁 Document Management")

    uploaded_file = st.file_uploader(
        "Upload PDF or TXT",
        type=["pdf", "txt"],
    )

    if st.button(
        "⬆️ Upload & Index",
        use_container_width=True,
    ):

        if uploaded_file:

            with st.spinner(
                "Uploading and indexing document..."
            ):

                upload_result = upload_document(
                    uploaded_file
                )

            if upload_result:

                st.success(
                    "Document indexed successfully!"
                )

                st.json(upload_result)

                st.rerun()

        else:

            st.warning(
                "Please select a document first."
            )

    # REFRESH DOCUMENTS

    if st.button(
        "🔄 Refresh Documents",
        use_container_width=True,
    ):

        st.session_state.refresh_documents = True

        st.rerun()

    # DOCUMENT LIST

    documents_data = api_get(
        "/documents"
    )

    if documents_data:

        st.caption(
            f"Total documents: "
            f"{documents_data.get('total_documents', 0)}"
        )

        for document in documents_data.get(
            "documents",
            [],
        ):

            st.write(
                "📄 "
                + document.get(
                    "filename",
                    "Unknown file",
                )
            )

    st.divider()

    st.caption(
        "Built with FastAPI • LangChain • ChromaDB • RAGAS"
    )


# =====================================================
# MAIN APPLICATION
# =====================================================

st.title("🤖 RAGAS AI Assistant")

st.markdown(
    "Ask questions from your documents and evaluate "
    "your Retrieval Augmented Generation system."
)


# =====================================================
# TABS
# =====================================================

chat_tab, evaluation_tab, reports_tab = st.tabs([
    "💬 AI Chat",
    "📊 Evaluation",
    "📄 Reports",
])


# =====================================================
# TAB 1: AI CHAT
# =====================================================

with chat_tab:

    st.subheader(
        "Chat with your Documents"
    )

    if st.session_state.session_id:

        st.caption(
            f"Active Session: "
            f"{st.session_state.session_id}"
        )

    # DISPLAY CHAT MESSAGES

    for message in st.session_state.messages:

        role = message.get(
            "role",
            "assistant",
        )

        content = message.get(
            "content",
            "",
        )

        with st.chat_message(role):

            st.markdown(content)

            display_sources(
                message.get(
                    "sources",
                    [],
                )
            )

    # CHAT INPUT

    question = st.chat_input(
        "Ask something about your documents..."
    )

    if question:

        with st.spinner(
            "AI is thinking..."
        ):

            send_message(question)

        st.rerun()

    # PERSISTENT DEBUG RESPONSE
    # This is outside the question condition.

    if st.session_state.debug_response is not None:

        with st.expander(
            "🔍 Debug: Backend API Response",
            expanded=True,
        ):

            st.caption(
                f"Backend URL: {API_BASE_URL}"
            )

            st.caption(
                f"Question: "
                f"{st.session_state.debug_question}"
            )

            st.json(
                st.session_state.debug_response
            )

    elif st.session_state.debug_question:

        with st.expander(
            "🔍 Debug: Backend API Response",
            expanded=True,
        ):

            st.caption(
                f"Backend URL: {API_BASE_URL}"
            )

            st.warning(
                "Backend returned no JSON response. "
                "Check the API error above."
            )


# =====================================================
# TAB 2: RAGAS EVALUATION
# =====================================================

with evaluation_tab:

    st.subheader(
        "📊 RAGAS Evaluation Dashboard"
    )

    st.write(
        "Evaluate your chatbot using the saved evaluation dataset."
    )

    st.warning(
        "Evaluation makes LLM API calls and may take some time."
    )

    if st.button(
        "🚀 Run RAGAS Evaluation",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Running RAGAS evaluation. Please wait..."
        ):

            evaluation_response = api_post(
                "/evaluation/run"
            )

        if evaluation_response:

            st.session_state.evaluation_result = (
                evaluation_response.get(
                    "evaluation"
                )
            )

            st.success(
                "Evaluation completed successfully!"
            )

    # DISPLAY EVALUATION

    evaluation = st.session_state.evaluation_result

    if evaluation:

        st.divider()

        st.subheader(
            "Evaluation Results"
        )

        st.json(evaluation)

        if isinstance(evaluation, dict):

            metrics = evaluation.get(
                "average_scores"
            )

            if not isinstance(metrics, dict):

                metrics = evaluation.get(
                    "metrics"
                )

            if isinstance(metrics, dict) and metrics:

                cols = st.columns(
                    len(metrics)
                )

                for col, (metric, score) in zip(
                    cols,
                    metrics.items(),
                ):

                    try:

                        with col:

                            st.metric(
                                label=metric.replace(
                                    "_",
                                    " ",
                                ).title(),

                                value=round(
                                    float(score),
                                    4,
                                ),
                            )

                    except (
                        ValueError,
                        TypeError,
                    ):

                        pass

        st.info(
            "Detailed evaluation output is displayed above."
        )

    else:

        st.info(
            "Run evaluation to see your RAGAS results here."
        )


# =====================================================
# TAB 3: REPORT GENERATION
# =====================================================

with reports_tab:

    st.subheader(
        "📄 Evaluation Reports"
    )

    st.write(
        "Generate JSON, CSV and PDF reports "
        "from the latest saved evaluation."
    )

    if st.button(
        "📑 Generate Reports",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Generating reports..."
        ):

            report_response = api_post(
                "/evaluation/reports/generate"
            )

        if report_response:

            st.session_state.generated_reports = (
                report_response
            )

            st.success(
                "Reports generated successfully!"
            )

    # DISPLAY GENERATED REPORTS

    report_data = st.session_state.generated_reports

    if report_data:

        st.json(report_data)

        filenames = find_report_filenames(
            report_data
        )

        if filenames:

            st.divider()

            st.subheader(
                "⬇️ Download Reports"
            )

            for filename in filenames:

                file_content = download_report(
                    filename
                )

                if file_content:

                    st.download_button(
                        label=(
                            "Download "
                            + Path(filename).suffix.upper()
                        ),

                        data=file_content,

                        file_name=filename,

                        mime={
                            ".json": "application/json",
                            ".csv": "text/csv",
                            ".pdf": "application/pdf",
                        }.get(
                            Path(filename).suffix.lower(),
                            "application/octet-stream",
                        ),

                        key=f"download_{filename}",

                        use_container_width=True,
                    )

        else:

            st.warning(
                "Report filenames were not found "
                "in the API response. "
                "Check the response shown above."
            )

    else:

        st.info(
            "First run RAGAS evaluation, "
            "then generate reports."
        )


# =====================================================
# FOOTER
# =====================================================

st.divider()

st.caption(
    "RAGAS AI Assistant | "
    "FastAPI + Streamlit + LangChain + ChromaDB"
)
