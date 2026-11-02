
import sqlite3
from pathlib import Path


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "chat_history.db"


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

def initialize_chat_database():

    with get_connection() as connection:

        # Chat messages table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Chat sessions table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT 'New Chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Index for faster message retrieval
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_session
            ON chat_messages(session_id, id)
        """)

        # Migrate existing sessions into chat_sessions
        connection.execute("""
            INSERT OR IGNORE INTO chat_sessions (
                session_id,
                title,
                created_at,
                updated_at
            )
            SELECT
                session_id,
                'New Chat',
                MIN(created_at),
                MAX(created_at)
            FROM chat_messages
            GROUP BY session_id
        """)


# --------------------------------------------------
# SAVE MESSAGE
# --------------------------------------------------

def save_message(session_id: str, role: str, content: str):

    if role not in ("user", "assistant"):
        raise ValueError("Invalid message role.")

    with get_connection() as connection:

        # Create session if it does not exist
        connection.execute(
            """
            INSERT OR IGNORE INTO chat_sessions (session_id)
            VALUES (?)
            """,
            (session_id,)
        )

        # Save message
        connection.execute(
            """
            INSERT INTO chat_messages (
                session_id,
                role,
                content
            )
            VALUES (?, ?, ?)
            """,
            (session_id, role, content),
        )

        # Update session activity
        connection.execute(
            """
            UPDATE chat_sessions
            SET updated_at = CURRENT_TIMESTAMP
            WHERE session_id = ?
            """,
            (session_id,)
        )


# --------------------------------------------------
# GET RECENT CHAT HISTORY
# --------------------------------------------------

def get_chat_history(session_id: str, limit: int = 10):

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT role, content
            FROM (
                SELECT id, role, content
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            )
            ORDER BY id ASC
            """,
            (session_id, limit),
        ).fetchall()

    return [
        {
            "role": row["role"],
            "content": row["content"],
        }
        for row in rows
    ]


# --------------------------------------------------
# GET COMPLETE SESSION MESSAGES
# --------------------------------------------------

def get_session_messages(session_id: str):

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT role, content, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()

    return [dict(row) for row in rows]


# --------------------------------------------------
# GET ALL CHAT SESSIONS
# --------------------------------------------------

def get_all_sessions():

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT
                s.session_id,
                s.title,
                COUNT(m.id) AS total_messages,
                s.created_at AS started_at,
                s.updated_at AS last_activity
            FROM chat_sessions s
            LEFT JOIN chat_messages m
                ON s.session_id = m.session_id
            GROUP BY s.session_id
            ORDER BY s.updated_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


# --------------------------------------------------
# DELETE COMPLETE CHAT SESSION
# --------------------------------------------------

def delete_chat_session(session_id: str):

    with get_connection() as connection:

        connection.execute(
            """
            DELETE FROM chat_messages
            WHERE session_id = ?
            """,
            (session_id,)
        )

        cursor = connection.execute(
            """
            DELETE FROM chat_sessions
            WHERE session_id = ?
            """,
            (session_id,)
        )

    return cursor.rowcount


# --------------------------------------------------
# RENAME CHAT SESSION
# --------------------------------------------------

def rename_chat_session(session_id: str, new_title: str):

    new_title = new_title.strip()

    if not new_title:
        raise ValueError("Session title cannot be empty.")

    if len(new_title) > 100:
        raise ValueError("Session title cannot exceed 100 characters.")

    with get_connection() as connection:

        cursor = connection.execute(
            """
            UPDATE chat_sessions
            SET title = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE session_id = ?
            """,
            (new_title, session_id)
        )

    return cursor.rowcount


# --------------------------------------------------
# SEARCH CHAT HISTORY
# --------------------------------------------------

def search_chat_history(query: str):

    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty.")

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT
                m.session_id,
                s.title,
                m.role,
                m.content,
                m.created_at
            FROM chat_messages m
            LEFT JOIN chat_sessions s
                ON m.session_id = s.session_id
            WHERE m.content LIKE ? ESCAPE '\\'
            ORDER BY m.id DESC
            LIMIT 100
            """,
            (
                "%" + query.replace("\\", "\\\\")
                           .replace("%", "\\%")
                           .replace("_", "\\_") + "%",
            )
        ).fetchall()

    return [dict(row) for row in rows]


# --------------------------------------------------
# CLEAR CHAT HISTORY
# --------------------------------------------------

def clear_chat_history(session_id: str):

    with get_connection() as connection:

        cursor = connection.execute(
            """
            DELETE FROM chat_messages
            WHERE session_id = ?
            """,
            (session_id,)
        )

        deleted_messages = cursor.rowcount

        connection.execute(
            """
            UPDATE chat_sessions
            SET updated_at = CURRENT_TIMESTAMP
            WHERE session_id = ?
            """,
            (session_id,)
        )

    return deleted_messages
