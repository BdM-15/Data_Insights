"""
notes.py

Handles storage and retrieval of user notes for the chat utility.
Notes are stored in the app_logs.user_notes table in PostgreSQL.
Designed for modular use and easy integration with Streamlit UI.

Author: Data_Insights Team
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import config  # Centralized config access

DATABASE_URL = config.DATABASE_URL
engine = create_engine(DATABASE_URL)

def add_note(note_text: str, page: str, tab: str, user_id: Optional[str] = None, session_id: Optional[str] = None) -> int:
    """
    Add a new user note to the database.
    Returns the new note's ID.
    """
    insert_sql = text('''
        INSERT INTO app_logs.user_notes (note_text, user_id, session_id, page, tab, created_at)
        VALUES (:note_text, :user_id, :session_id, :page, :tab, :created_at)
        RETURNING id
    ''')
    try:
        with engine.begin() as conn:
            result = conn.execute(insert_sql, {
                "note_text": note_text,
                "user_id": user_id,
                "session_id": session_id,
                "page": page,
                "tab": tab,
                "created_at": datetime.utcnow()
            })
            return result.scalar()
    except SQLAlchemyError as e:
        print(f"[Notes] Failed to add note: {e}")
        return -1

def get_notes(page: str, tab: str, user_id: Optional[str] = None, session_id: Optional[str] = None) -> List[dict]:
    """
    Retrieve notes for a given page/tab (optionally filtered by user/session).
    Returns a list of dicts with note details.
    """
    select_sql = text('''
        SELECT id, note_text, user_id, session_id, created_at, last_used_in_chat_at
        FROM app_logs.user_notes
        WHERE page = :page AND tab = :tab
        ORDER BY created_at DESC
    ''')
    try:
        with engine.begin() as conn:
            result = conn.execute(select_sql, {"page": page, "tab": tab})
            return [dict(row) for row in result.mappings()]
    except SQLAlchemyError as e:
        print(f"[Notes] Failed to fetch notes: {e}")
        return []

# Reason: This module provides modular note storage/retrieval for UI and chat context enrichment.
