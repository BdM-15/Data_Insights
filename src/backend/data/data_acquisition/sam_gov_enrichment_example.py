"""
Sample enrichment pipeline for SAM.gov solicitations → Document model
"""
from datetime import datetime
from typing import List, Dict, Any
from src.backend.data.models.data_models import Document
# from your_embedding_module import generate_embedding  # Implement with Ollama or local LLM

def sam_opportunity_to_document(sam_row: Dict[str, Any]) -> Document:
    """
    Convert a SAM.gov opportunity row to a Document model for RAG/semantic search.
    Args:
        sam_row: Dict with SAM.gov opportunity fields
    Returns:
        Document instance
    """
    return Document(
        document_id=sam_row["noticeId"],
        related_contract_id=sam_row.get("awardID") or None,
        text=sam_row.get("description") or "",
        embedding=None,  # Fill with generate_embedding(sam_row.get("description", ""))
        source_url=sam_row.get("url"),
        document_type="SAM.gov Solicitation",
        created_at=sam_row.get("postedDate", datetime.utcnow()),
        updated_at=sam_row.get("updatedDate", datetime.utcnow()),
        metadata={
            "naics": sam_row.get("naics"),
            "agency": sam_row.get("agency"),
            "response_due_date": sam_row.get("responseDueDate"),
            "award_type": sam_row.get("awardType"),
            # ...add all other relevant fields
        }
    )

# Example usage after fetching and deduplication:
# documents = [sam_opportunity_to_document(row) for row in sam_opportunities]
# Store in DB (as JSONB + vector)
