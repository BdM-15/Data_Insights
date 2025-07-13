"""
Capture Intelligence Agent

Clean implementation using LangGraph and MCP servers for defense contracting business intelligence.
Provides expert-level consultation for capture management and competitive analysis.
"""

from .capture_intelligence_agent import CaptureIntelligenceAgent

# Create alias for backward compatibility
class LangGraphOrchestratorAgent(CaptureIntelligenceAgent):
    """
    Alias for CaptureIntelligenceAgent to maintain backward compatibility.
    Uses modern LangGraph for tool orchestration and MCP servers for data access.
    """
    pass

# Legacy alias
class ModernAgent(CaptureIntelligenceAgent):
    """Legacy alias for backward compatibility."""
    pass
