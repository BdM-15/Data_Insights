"""
Comprehensive Chat Logging System

This module provides detailed logging for LLM interactions, including:
- Tool usage tracking
- Agent reasoning capture
- Performance metrics
- Error analysis
- Conversation context

Designed for debugging, optimization, and behavior analysis.
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Import database config variables directly
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))
from config import PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD

logger = logging.getLogger(__name__)

class ChatLogger:
    """Comprehensive chat interaction logger for LLM behavior analysis."""
    
    def __init__(self):
        self.connection = None
        self.session_id = str(uuid.uuid4())
        self._connect_to_database()
    
    def _connect_to_database(self):
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                database=PG_DATABASE,
                user=PG_USER,
                password=PG_PASSWORD
            )
            logger.info("Chat logger database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database for chat logging: {e}")
            self.connection = None
    
    def start_interaction(self, user_query: str, model_name: str, temperature: float, 
                         system_prompt: str, page: str = "ai_chat", tab: str = "main",
                         conversation_context: Dict = None) -> str:
        """
        Start logging a new chat interaction.
        
        Args:
            user_query: The user's input
            model_name: LLM model being used
            temperature: Model temperature setting
            system_prompt: System prompt provided to the model
            page: UI page where interaction occurred
            tab: UI tab where interaction occurred
            conversation_context: Previous conversation context
            
        Returns:
            Interaction ID for tracking this specific interaction
        """
        interaction_id = str(uuid.uuid4())
        
        if not self.connection:
            logger.warning("No database connection for chat logging")
            return interaction_id
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO app_logs.chat_logs (
                        user_query, model_name, model_temperature, system_prompt,
                        page, tab, session_id, conversation_context, status,
                        created_at, llm_response, response_type
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id
                """, (
                    user_query, model_name, temperature, system_prompt,
                    page, tab, self.session_id, 
                    json.dumps(conversation_context) if conversation_context else None,
                    'processing', datetime.now(), '', 'processing'
                ))
                
                result = cursor.fetchone()
                interaction_id = str(result[0]) if result else interaction_id
                self.connection.commit()
                
                logger.info(f"Started logging interaction {interaction_id}")
                
        except Exception as e:
            logger.error(f"Failed to start interaction logging: {e}")
            if self.connection:
                self.connection.rollback()
        
        return interaction_id
    
    def log_tool_usage(self, interaction_id: str, tool_name: str, tool_input: Dict, 
                      tool_result: Any, execution_time_ms: int, success: bool = True,
                      error_details: str = None):
        """
        Log individual tool usage within an interaction.
        
        Args:
            interaction_id: ID of the interaction
            tool_name: Name of the tool that was used
            tool_input: Input parameters passed to the tool
            tool_result: Result returned by the tool
            execution_time_ms: Time taken for tool execution
            success: Whether the tool execution was successful
            error_details: Error information if tool failed
        """
        if not self.connection:
            return
            
        try:
            with self.connection.cursor() as cursor:
                # Get current tools_used and tool_results
                cursor.execute("""
                    SELECT tools_used, tool_results FROM app_logs.chat_logs 
                    WHERE id = %s
                """, (interaction_id,))
                
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"Interaction {interaction_id} not found for tool logging")
                    return
                
                current_tools = result[0] or []
                current_results = result[1] or {}
                
                # Add new tool usage
                tool_entry = {
                    "name": tool_name,
                    "input": tool_input,
                    "execution_time_ms": execution_time_ms,
                    "success": success,
                    "timestamp": datetime.now().isoformat()
                }
                
                if error_details:
                    tool_entry["error"] = error_details
                
                current_tools.append(tool_entry)
                current_results[f"{tool_name}_{len(current_tools)}"] = {
                    "result": str(tool_result)[:5000],  # Limit size
                    "success": success
                }
                
                # Update the record
                cursor.execute("""
                    UPDATE app_logs.chat_logs 
                    SET tools_used = %s, tool_results = %s
                    WHERE id = %s
                """, (json.dumps(current_tools), json.dumps(current_results), interaction_id))
                
                self.connection.commit()
                logger.debug(f"Logged tool usage: {tool_name} for interaction {interaction_id}")
                
        except Exception as e:
            logger.error(f"Failed to log tool usage: {e}")
            if self.connection:
                self.connection.rollback()
    
    def log_agent_reasoning(self, interaction_id: str, reasoning_step: str, 
                           step_type: str, content: Dict):
        """
        Log agent reasoning steps and decision making process.
        
        Args:
            interaction_id: ID of the interaction
            reasoning_step: Description of the reasoning step
            step_type: Type of reasoning (planning, execution, reflection, etc.)
            content: Detailed reasoning content
        """
        if not self.connection:
            return
            
        try:
            with self.connection.cursor() as cursor:
                # Get current agent_reasoning
                cursor.execute("""
                    SELECT agent_reasoning FROM app_logs.chat_logs 
                    WHERE id = %s
                """, (interaction_id,))
                
                result = cursor.fetchone()
                if not result:
                    return
                
                current_reasoning = result[0] or {"steps": []}
                
                # Add new reasoning step
                reasoning_entry = {
                    "step": reasoning_step,
                    "type": step_type,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }
                
                if "steps" not in current_reasoning:
                    current_reasoning["steps"] = []
                
                current_reasoning["steps"].append(reasoning_entry)
                
                # Update the record
                cursor.execute("""
                    UPDATE app_logs.chat_logs 
                    SET agent_reasoning = %s
                    WHERE id = %s
                """, (json.dumps(current_reasoning), interaction_id))
                
                self.connection.commit()
                logger.debug(f"Logged reasoning step for interaction {interaction_id}")
                
        except Exception as e:
            logger.error(f"Failed to log agent reasoning: {e}")
            if self.connection:
                self.connection.rollback()
    
    def complete_interaction(self, interaction_id: str, llm_response: str, 
                           total_time_ms: int, tokens_used: int = None,
                           success: bool = True, error_details: Dict = None,
                           response_type: str = "text"):
        """
        Complete and finalize an interaction log.
        
        Args:
            interaction_id: ID of the interaction
            llm_response: Final response from the LLM
            total_time_ms: Total processing time
            tokens_used: Number of tokens consumed
            success: Whether the interaction was successful
            error_details: Error information if failed
            response_type: Type of response (text, code, error, etc.)
        """
        if not self.connection:
            return
            
        try:
            with self.connection.cursor() as cursor:
                status = 'success' if success else 'error'
                
                cursor.execute("""
                    UPDATE app_logs.chat_logs 
                    SET llm_response = %s, processing_time_ms = %s, tokens_used = %s,
                        status = %s, error_details = %s, response_type = %s
                    WHERE id = %s
                """, (
                    llm_response, total_time_ms, tokens_used, status,
                    json.dumps(error_details) if error_details else None,
                    response_type, interaction_id
                ))
                
                self.connection.commit()
                logger.info(f"Completed interaction logging: {interaction_id} ({status})")
                
        except Exception as e:
            logger.error(f"Failed to complete interaction logging: {e}")
            if self.connection:
                self.connection.rollback()
    
    def log_user_feedback(self, interaction_id: str, rating: int, notes: str = None):
        """
        Log user feedback for an interaction.
        
        Args:
            interaction_id: ID of the interaction
            rating: User rating (1-5)
            notes: Optional feedback notes
        """
        if not self.connection:
            return
            
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE app_logs.chat_logs 
                    SET user_feedback = %s, feedback_notes = %s
                    WHERE id = %s
                """, (rating, notes, interaction_id))
                
                self.connection.commit()
                logger.info(f"Logged user feedback for interaction {interaction_id}: {rating}/5")
                
        except Exception as e:
            logger.error(f"Failed to log user feedback: {e}")
            if self.connection:
                self.connection.rollback()
    
    def get_interaction_analytics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get analytics about recent interactions.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Analytics data
        """
        if not self.connection:
            return {}
            
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_interactions,
                        AVG(processing_time_ms) as avg_processing_time,
                        AVG(tokens_used) as avg_tokens,
                        AVG(user_feedback) as avg_rating,
                        COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count,
                        COUNT(CASE WHEN tools_used IS NOT NULL THEN 1 END) as tool_usage_count,
                        jsonb_agg(DISTINCT model_name) as models_used
                    FROM app_logs.chat_logs 
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                """, (days,))
                
                result = cursor.fetchone()
                return dict(result) if result else {}
                
        except Exception as e:
            logger.error(f"Failed to get interaction analytics: {e}")
            return {}
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Chat logger database connection closed")

# Global chat logger instance
chat_logger = ChatLogger()
