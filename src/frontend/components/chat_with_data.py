"""
Reusable Streamlit component for Data_Insights Chat/Notes/Visualization UI.

- Use this module to render the chat, notes, and visualization UI in any Streamlit page.
- All backend API calls and session context are handled internally.

Usage:
    from src.frontend.components.chat_with_data import render_chat_with_data
    render_chat_with_data(page="market_overview", tab="main")
"""

import streamlit as st
import requests
import uuid

API_URL = "http://localhost:8001"  # Adjust if backend runs elsewhere


@st.fragment
def render_notes_section(page, tab, user_id, session_id):
    """
    Render the notes UI for the Data_Insights app.

    Args:
        page: Page context for notes
        tab: Tab context for notes
        user_id: User identifier
        session_id: Session identifier
    """
    # --- Notes Section ---
    # Divider for visual separation
    st.divider()
    st.subheader("Notes")
    # Stateless notes UI: always fetch from backend, minimal session state
    if "selected_note_id" not in st.session_state:
        st.session_state["selected_note_id"] = None
    if "edit_note_text" not in st.session_state:
        st.session_state["edit_note_text"] = ""

    # Always fetch notes from backend, and re-fetch after any action
    def fetch_notes():
        resp = requests.get(f"{API_URL}/notes", params={"page": page, "tab": tab, "user_id": user_id, "session_id": session_id})
        return resp.json().get("notes", []) if resp.ok else []

    # --- Fetch notes ---
    notes = fetch_notes()

    # --- Handle update/cancel for edit form before rendering any forms ---
    note_id = st.session_state.get("selected_note_id")
    note_to_edit = next((n for n in notes if n["id"] == note_id), None) if note_id else None
    edit_result = None
    if note_to_edit and st.session_state.get("_edit_form_submitted"):
        # This block is only entered after a form submit, so we process and clear state
        if st.session_state.get("_edit_form_action") == "update":
            update_resp = requests.put(f"{API_URL}/notes/update", json={"id": note_id, "note_text": st.session_state["edit_note_text"]})
            if not update_resp.ok:
                st.error("Failed to update note.")
            st.session_state["selected_note_id"] = None
            st.session_state["edit_note_text"] = ""
            notes = fetch_notes()
        elif st.session_state.get("_edit_form_action") == "cancel":
            st.session_state["selected_note_id"] = None
            st.session_state["edit_note_text"] = ""
        st.session_state["_edit_form_submitted"] = False
        st.session_state["_edit_form_action"] = None
        note_id = None
        note_to_edit = None

    # --- Show either Add Note or Edit Note form (never both) ---
    if note_to_edit:
        with st.form(f"edit_note_form_{note_id}", clear_on_submit=True):
            edit_text = st.text_area(
                "Edit Note",
                value=st.session_state["edit_note_text"],
                key=f"edit_note_text_area_{note_id}"
            )
            col_update, col_cancel = st.columns([1, 1])
            update_clicked = col_update.form_submit_button("Update Note")
            cancel_clicked = col_cancel.form_submit_button("Cancel Edit")
            if update_clicked:
                st.session_state["edit_note_text"] = edit_text
                st.session_state["_edit_form_submitted"] = True
                st.session_state["_edit_form_action"] = "update"
                st.experimental_rerun()
            elif cancel_clicked:
                st.session_state["_edit_form_submitted"] = True
                st.session_state["_edit_form_action"] = "cancel"
                st.experimental_rerun()
    else:
        with st.form("add_note_form", clear_on_submit=True):
            note_text = st.text_area(
                "Add a new note for additional context.  Notes will serve as unique context for the LLM to consider in its response.",
                "",
                key="add_note_text",
                height=68
            )
            add_clicked = st.form_submit_button("Add Note")
            if add_clicked and note_text.strip():
                add_resp = requests.post(f"{API_URL}/note", json={"note_text": note_text.strip(), "page": page, "tab": tab, "user_id": user_id, "session_id": session_id})
                if not add_resp.ok:
                    st.error("Failed to add note.")
                notes = fetch_notes()

    # --- Notes List (always below form) ---
    for note in notes:
        if st.session_state.get("selected_note_id") is None:
            col1, col2, col3 = st.columns([8, 1, 1])
            with col1:
                st.markdown(f'{note["note_text"]}')
            with col2:
                if st.button("✏️", key=f"edit_{note['id']}"):
                    st.session_state["selected_note_id"] = note["id"]
                    st.session_state["edit_note_text"] = note["note_text"]
            with col3:
                if st.button("🗑️", key=f"delete_{note['id']}"):
                    del_resp = requests.delete(f"{API_URL}/notes/delete", json={"id": note["id"]})
                    if not del_resp.ok:
                        st.error("Failed to delete note.")
                    # Clear edit state if deleting the note being edited
                    if st.session_state.get("selected_note_id") == note["id"]:
                        st.session_state["selected_note_id"] = None
                        st.session_state["edit_note_text"] = ""
                    notes = fetch_notes()

def render_chat_with_data(page: str = "market_overview", tab: str = "main"):
    """
    Render the chat, notes, and visualization UI for the Data_Insights app.

    Args:
        page: Page context for notes/chat logging
        tab: Tab context for notes/chat logging
    """
    # --- Session and user context ---
    session_id = st.session_state.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        st.session_state["session_id"] = session_id
    user_id = st.session_state.get("user_id", "demo_user")

    render_notes_section(page, tab, user_id, session_id)

    # --- Chat UI (fragmented for partial rerun, no full rerun) ---
    @st.fragment
    def chat_section():
        st.subheader("Ask a question about your data")
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []
        if "chat_input" not in st.session_state:
            st.session_state["chat_input"] = ""

        # Chat input form (so only this fragment reruns)
        with st.form("chat_input_form", clear_on_submit=True):
            user_prompt = st.text_input("Your question:", st.session_state["chat_input"], key="chat_user_prompt")
            # Optional: model selector (default: mistral)
            model = st.selectbox("Model", ["mistral", "llama2", "codellama"], key="chat_model")
            send_clicked = st.form_submit_button("Send")
            if send_clicked and user_prompt.strip():
                # Fetch notes for context
                notes_resp = requests.get(f"{API_URL}/notes", params={"page": page, "tab": tab, "user_id": user_id, "session_id": session_id})
                notes = notes_resp.json().get("notes", []) if notes_resp.ok else []
                notes_text = "\n".join([n["note_text"] for n in notes])
                payload = {
                    "user_prompt": user_prompt,
                    "page": page,
                    "tab": tab,
                    "session_id": session_id,
                    "user_id": user_id,
                    "notes": notes_text,
                    "model": model
                }
                # Use MCP LLM endpoint for real LLM response
                resp = requests.post(f"{API_URL}/mcp/llm/chat", json=payload)
                if resp.ok:
                    answer = resp.json().get("answer", "[No answer returned]")
                    vis_url = resp.json().get("visualization_url")
                    st.session_state["chat_history"].append({"user": user_prompt, "bot": answer, "visualization_url": vis_url})
                else:
                    st.session_state["chat_history"].append({"user": user_prompt, "bot": "[Error: Backend unavailable]", "visualization_url": None})
                st.session_state["chat_input"] = ""
            else:
                st.session_state["chat_input"] = user_prompt

        # Display chat history (latest at bottom)
        for entry in st.session_state["chat_history"]:
            st.markdown(f"**You:** {entry['user']}")
            st.markdown(f"**Roberto:** {entry['bot']}")
            if entry.get("visualization_url"):
                st.image(entry["visualization_url"], caption="Visualization", use_column_width=True)

    chat_section()
    st.divider()

