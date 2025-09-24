"""
Agent Logger Module

Handles logging and retrieval of agent/LLM interactions for analytics and context augmentation.
"""

import asyncpg
import os
from typing import Optional, Any, List, Dict
from datetime import datetime

class AgentLogger:
    """
    Handles logging and retrieval of agent/LLM interactions in the app_logs.agent_interaction_log table.
    """
    _log_db_dsn = os.getenv("AGENT_LOG_DB_DSN")

    async def log_interaction(
        self,
        user_id: Optional[str],
        session_id: Optional[str],
        user_prompt: str,
        tool_name: Optional[str],
        tool_args: Any,
        tool_result: Any,
        llm_output: str,
        error: Optional[str],
        debug_info: Any,
        context: Any
    ):
        """
        Log an agent/LLM interaction to the app_logs.agent_interaction_log table.
        """
        try:
            conn = await asyncpg.connect(self._log_db_dsn)
            await conn.execute(
                """
                INSERT INTO app_logs.agent_interaction_log
                (user_id, session_id, user_prompt, tool_name, tool_args, tool_result, llm_output, error, debug_info, context)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                user_id,
                session_id,
                user_prompt,
                tool_name,
                tool_args,
                tool_result,
                llm_output,
                error,
                debug_info,
                context
            )
            await conn.close()
        except Exception as e:
            print(f"Failed to log agent interaction: {e}")

    async def get_recent_logs(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent agent/LLM interactions for a user/session for analytics or context.
        """
        try:
            conn = await asyncpg.connect(self._log_db_dsn)
            rows = await conn.fetch(
                """
                SELECT * FROM app_logs.agent_interaction_log
                WHERE ($1 IS NULL OR user_id = $1)
                  AND ($2 IS NULL OR session_id = $2)
                ORDER BY timestamp_utc DESC
                LIMIT $3
                """,
                user_id, session_id, limit
            )
            await conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Failed to retrieve agent logs: {e}")
            return []

    async def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """
        Return basic analytics (total interactions, error rate, etc.) for dashboard.
        """
        try:
            conn = await asyncpg.connect(self._log_db_dsn)
            result = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) AS total_interactions,
                    COUNT(*) FILTER (WHERE error IS NOT NULL) AS error_count
                FROM app_logs.agent_interaction_log
                WHERE timestamp_utc >= NOW() - INTERVAL '$1 days'
                """,
                days
            )
            await conn.close()
            return dict(result) if result else {}
        except Exception as e:
            print(f"Failed to get analytics: {e}")
            return {}
