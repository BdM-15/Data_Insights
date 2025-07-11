"""
Orchestrator Router API with Dynamic Tool Discovery and Flexible Routing.

This module implements Phase 1 of the LLM-First Architecture:
- Dynamic tool discovery instead of hard-coded lists
- Intelligent routing based on LLM reasoning
- Self-aware system capabilities
- Context-aware prompt engineering
"""
import asyncio
from fastapi import APIRouter, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
from backend.data.models.data_models import AgenticIntent, FlexibleIntent, ServiceDiscoveryResponse, DynamicToolResponse
from backend.ai.mcp_servers.service_discovery.service_discovery import get_service_discovery
import requests
import json
import re
from datetime import datetime
import logging
import os
import aiohttp

router = APIRouter()

LLAMA3_MODEL = "llama3.1:8b"
OLLAMA_URL = "http://localhost:11434/api/chat"

logger = logging.getLogger("orchestrator_router")
logger.setLevel(logging.INFO)

try:
    LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'logs'))
    LOG_PATH = os.path.join(LOG_DIR, 'orchestrator_router.log')
    os.makedirs(LOG_DIR, exist_ok=True)
    file_handler = logging.FileHandler(LOG_PATH)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    for h in logger.handlers[:]:
        logger.removeHandler(h)
    logger.addHandler(file_handler)
    print(f"[OrchestratorRouter] Logging to {LOG_PATH}")
    logger.info("[OrchestratorRouter] Logger initialized and ready.")
except Exception as log_setup_exc:
    print(f"[OrchestratorRouter] Logger setup failed: {log_setup_exc}")


class FlexibleRouteRequest(BaseModel):
    """Request model for flexible routing."""
    prompt: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    page: Optional[str] = None
    tab: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


def generate_dynamic_prompt(available_tools: List[Dict[str, Any]], user_prompt: str, context: Dict[str, Any] = None) -> str:
    """
    Generate a dynamic prompt with real-time system state and available tools.
    
    Args:
        available_tools: List of dynamically discovered tools
        user_prompt: User's request
        context: Additional context information
        
    Returns:
        Formatted prompt for LLM
    """
    # Get service discovery instance
    service_discovery = get_service_discovery()
    system_status = service_discovery.get_system_status()
    
    # Format tools for prompt
    tools_description = []
    for tool in available_tools:
        tool_desc = f"- **{tool['name']}**: {tool['description']}"
        if tool.get('examples'):
            examples = ", ".join(tool['examples'][:2])  # Limit to 2 examples
            tool_desc += f" (Examples: {examples})"
        tools_description.append(tool_desc)
    
    tools_text = "\n".join(tools_description)
    
    # Create context information
    context_info = []
    if context:
        for key, value in context.items():
            context_info.append(f"- {key}: {value}")
    
    context_text = "\n".join(context_info) if context_info else "No additional context provided"
    
    # Build dynamic prompt
    prompt = f"""
You are an AI consultant specializing in defense contracting and business intelligence. Your role is to help professionals in capture management, business development, and contract analysis make informed decisions.

**CURRENT SYSTEM STATUS**
- Active Servers: {system_status['healthy_servers']}/{system_status['total_servers']}
- Available Capabilities: {system_status['total_capabilities']}
- Last Updated: {system_status.get('discovery_time', 'N/A')}

**AVAILABLE TOOLS & CAPABILITIES**
{tools_text}

**CONTEXT**
{context_text}

**YOUR APPROACH**
You have access to powerful tools that can query databases, analyze contracts, and generate insights. When a user asks a question:

1. **Understand the Intent**: What does the user really need to know? Are they exploring data structure, seeking specific information, or looking for strategic insights?

2. **Choose Your Response Style**:
   - **Conversational**: For general questions, explanations, or strategic advice - respond naturally in human language
   - **Tool-Assisted**: When specific data, analysis, or system capabilities are needed - use the appropriate tools

3. **For Tool Usage**: When you need to use tools, respond with a JSON structure like this:
```json
{{
    "intent": "<what_user_wants_to_accomplish>",
    "approach": "<conversational|single_tool|multi_step|workflow>",
    "reasoning": "<your_thinking_process>",
    "confidence": <0.0_to_1.0>,
    "primary_tool": "<tool_name>",
    "tool_sequence": [
        {{"tool": "<tool_name>", "parameters": {{}}, "description": "<purpose>"}}
    ],
    "parameters": {{"<tool_parameters>": "values"}},
    "expected_output": "<what_you_expect_to_deliver>"
}}
```

4. **Processing Results**: After using tools, interpret and present results in natural, business-focused language. Think like a consultant presenting findings to a client.

**REAL-WORLD EXAMPLES**

*User*: "What tables are available in the database?"
*You*: Use schema_introspection tool, then respond conversationally: "I found several key datasets in your system: prime awards, subawards, quarterly summaries, and various filter tables for agencies, contractors, and codes. These cover the main contracting data you'd typically need for capture analysis. Would you like me to dive deeper into any specific area?"

*User*: "Show me the top 10 contractors by total obligations"
*You*: Use data_query tool with appropriate SQL, then present: "Based on the latest data, here are the top 10 contractors by total obligations: [formatted list with context about what this means for business development opportunities]"

*User*: "How do I identify good teaming partners?"
*You*: Respond conversationally with strategic advice, possibly suggesting specific data queries to support the analysis.

**DOMAIN EXPERTISE**
You understand:
- Defense acquisition processes and regulations
- Contract vehicles (IDIQs, GWACs, etc.)
- Opportunity qualification and capture planning
- Competitive intelligence and market analysis
- Teaming strategies and partnership development

**GUIDELINES**
- Always respond in clear, professional language
- Provide context and strategic insights with data
- Suggest follow-up questions or next steps
- Adapt your communication style to the user's expertise level
- Be transparent about limitations or uncertainties

User Request: {user_prompt}
"""
    
    return prompt


@router.post("/discover_tools")
async def discover_tools() -> DynamicToolResponse:
    """
    Discover and return all available tools from running MCP servers.
    
    Returns:
        DynamicToolResponse with discovered tools and metadata
    """
    try:
        service_discovery = get_service_discovery()
        servers = service_discovery.discover_available_servers()
        tools = service_discovery.get_available_tools()
        
        response = DynamicToolResponse(
            tools=tools,
            total_tools=len(tools),
            server_count=len(servers),
            last_updated=datetime.now().isoformat()
        )
        
        logger.info(f"Tool discovery completed: {len(tools)} tools from {len(servers)} servers")
        return response
        
    except Exception as e:
        logger.error(f"Tool discovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"Tool discovery failed: {e}")


@router.get("/system_status")
async def get_system_status() -> ServiceDiscoveryResponse:
    """
    Get comprehensive system status including all servers and capabilities.
    
    Returns:
        ServiceDiscoveryResponse with system status
    """
    try:
        service_discovery = get_service_discovery()
        status = service_discovery.get_system_status()
        
        # Convert to response format
        servers_list = []
        for server_info in status.get('servers', []):
            servers_list.append({
                "name": server_info['name'],
                "port": server_info['port'],
                "status": server_info['status'],
                "capabilities": server_info.get('capabilities_count', 0),
                "last_health_check": None  # This field isn't in the current server_info
            })
        
        response = ServiceDiscoveryResponse(
            servers=servers_list,
            total_servers=status['total_servers'],
            healthy_servers=status['healthy_servers'],
            total_capabilities=status['total_capabilities'],
            discovery_time=status.get('discovery_time')
        )
        
        return response
        
    except Exception as e:
        logger.error(f"System status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"System status retrieval failed: {e}")


@router.post("/flexible_route")
async def flexible_route(request: FlexibleRouteRequest) -> JSONResponse:
    """
    Flexible routing endpoint that uses dynamic tool discovery and LLM reasoning.
    
    This endpoint implements intelligent, context-aware orchestration.
    """
    try:
        print(f"[DEBUG] Flexible routing started for: {request.prompt[:100]}...")
        logger.info(f"Flexible routing request: {request.prompt[:100]}...")
        
        print(f"[DEBUG] Getting service discovery...")
        # Get available tools dynamically
        service_discovery = get_service_discovery()
        
        print(f"[DEBUG] Getting available tools...")
        available_tools = service_discovery.get_available_tools()
        
        print(f"[DEBUG] Found {len(available_tools) if available_tools else 0} available tools")
        
        if not available_tools:
            print(f"[DEBUG] No tools available!")
            logger.warning("No tools available for routing")
            return JSONResponse(content={
                "response": "I'm sorry, but no tools are currently available. Please check that the MCP servers are running."
            })
        
        # Generate dynamic prompt with real-time system state
        llm_prompt = generate_dynamic_prompt(
            available_tools, 
            request.prompt, 
            request.context or {}
        )
        
        # Call Ollama LLM for intelligent routing decision
        ollama_payload = {
            "model": LLAMA3_MODEL,
            "messages": [
                {"role": "system", "content": llm_prompt},
                {"role": "user", "content": request.prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        llm_response = requests.post(OLLAMA_URL, json=ollama_payload, timeout=30)
        llm_response.raise_for_status()
        llm_content = llm_response.json().get("message", {}).get("content", "")
        
        # Try to parse as FlexibleIntent (tool execution mode)
        try:
            # First try to parse as direct JSON
            intent_json = json.loads(llm_content)
            flexible_intent = FlexibleIntent(**intent_json)
            
            # Log the LLM's reasoning
            logger.info(f"LLM reasoning: {flexible_intent.reasoning}")
            logger.info(f"LLM confidence: {flexible_intent.confidence}")
            logger.info(f"LLM approach: {flexible_intent.approach}")
            logger.info(f"Executing tool: {flexible_intent.primary_tool}")
            
            # Execute the intelligent routing
            result = execute_flexible_intent(flexible_intent, request, service_discovery)
            logger.info(f"Tool execution completed successfully")
            return result
            
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            json_pattern = r'```json\s*(.*?)\s*```'
            json_match = re.search(json_pattern, llm_content, re.DOTALL)
            
            if json_match:
                try:
                    json_content = json_match.group(1).strip()
                    logger.info(f"Extracted JSON from markdown: {json_content[:200]}...")
                    intent_json = json.loads(json_content)
                    flexible_intent = FlexibleIntent(**intent_json)
                    
                    # Log the LLM's reasoning
                    logger.info(f"LLM reasoning: {flexible_intent.reasoning}")
                    logger.info(f"LLM confidence: {flexible_intent.confidence}")
                    logger.info(f"LLM approach: {flexible_intent.approach}")
                    logger.info(f"Executing tool: {flexible_intent.primary_tool}")
                    
                    # Execute the intelligent routing
                    result = execute_flexible_intent(flexible_intent, request, service_discovery)
                    logger.info(f"Tool execution completed successfully")
                    return result
                    
                except Exception as json_parse_error:
                    logger.warning(f"Failed to parse extracted JSON: {json_parse_error}")
            
            # If not JSON, treat as conversational response
            logger.info(f"LLM provided conversational response: {str(llm_content)[:100]}...")
            return JSONResponse(content={"response": llm_content})
            
        except Exception as parse_error:
            # If not JSON, treat as conversational response
            logger.info(f"LLM provided conversational response: {str(parse_error)[:100]}...")
            return JSONResponse(content={"response": llm_content})
            
    except Exception as e:
        logger.error(f"Flexible routing failed: {e}")
        return JSONResponse(
            status_code=500, 
            content={"error": f"Flexible routing failed: {e}"}
        )


def execute_flexible_intent(
    intent: FlexibleIntent, 
    request: FlexibleRouteRequest,
    service_discovery
) -> JSONResponse:
    """
    Execute a flexible intent with intelligent tool orchestration.
    
    Args:
        intent: FlexibleIntent from LLM
        request: Original request
        service_discovery: Service discovery instance
        
    Returns:
        JSONResponse with execution results
    """
    try:
        logger.info(f"Executing intent: {intent.intent} with approach: {intent.approach}")
        
        if intent.approach == "conversational":
            # LLM decided this should be handled conversationally
            logger.info("Using conversational approach")
            return JSONResponse(content={
                "response": intent.reasoning,
                "confidence": intent.confidence
            })
            
        elif intent.approach == "single_tool":
            # Single tool execution
            logger.info(f"Using single tool approach with tool: {intent.primary_tool}")
            return execute_single_tool(intent, request, service_discovery)
            
        elif intent.approach == "multi_step":
            # Multi-step workflow
            return execute_multi_step_workflow(intent, request, service_discovery)
            
        elif intent.approach == "workflow":
            # Complex workflow orchestration
            return execute_complex_workflow(intent, request, service_discovery)
            
        else:
            logger.warning(f"Unknown approach: {intent.approach}")
            return JSONResponse(content={
                "response": f"I understand you want to {intent.intent}, but I'm not sure how to execute the '{intent.approach}' approach. Let me try a different method.",
                "confidence": 0.5
            })
            
    except Exception as e:
        logger.error(f"Intent execution failed: {e}")
        
        # Try fallback strategy if available
        if intent.fallback_strategy:
            logger.info(f"Attempting fallback strategy: {intent.fallback_strategy}")
            return JSONResponse(content={
                "response": f"My primary approach didn't work, but here's what I can tell you: {intent.fallback_strategy}",
                "confidence": 0.3
            })
        
        return JSONResponse(
            status_code=500,
            content={"error": f"Intent execution failed: {e}"}
        )


def execute_single_tool(
    intent: FlexibleIntent, 
    request: FlexibleRouteRequest,
    service_discovery
) -> JSONResponse:
    """Execute a single tool request."""
    try:
        logger.info(f"Looking for server with capability: {intent.primary_tool}")
        
        # Find the server that provides the primary tool
        server = service_discovery.get_server_for_capability(intent.primary_tool)
        
        if not server:
            logger.warning(f"No server found for capability: {intent.primary_tool}")
            return JSONResponse(content={
                "response": f"I couldn't find a server that provides the '{intent.primary_tool}' capability. Available tools might have changed.",
                "confidence": 0.2
            })
        
        logger.info(f"Found server: {server.name} for capability: {intent.primary_tool}")
        
        # Find the specific capability
        capability = None
        for cap in server.capabilities:
            if cap.name == intent.primary_tool:
                capability = cap
                break
        
        if not capability:
            logger.warning(f"Capability {intent.primary_tool} not found on server {server.name}")
            return JSONResponse(content={
                "response": f"The '{intent.primary_tool}' capability is not available on server {server.name}.",
                "confidence": 0.2
            })
        
        logger.info(f"Found capability: {capability.name} with endpoint: {capability.endpoint}")
        
        # Prepare the request payload
        payload = {
            **intent.parameters,
            "user_id": request.user_id,
            "session_id": request.session_id,
            "page": request.page,
            "tab": request.tab
        }
        
        # For single tool execution, check if parameters are in tool_sequence
        if intent.tool_sequence and len(intent.tool_sequence) > 0:
            tool_step = intent.tool_sequence[0]
            if tool_step.get("parameters"):
                logger.info(f"Adding parameters from tool_sequence: {tool_step['parameters']}")
                payload.update(tool_step["parameters"])
        
        # Add the original prompt if needed
        if "prompt" not in payload:
            payload["prompt"] = request.prompt
        
        logger.info(f"Executing {capability.method} request to {capability.endpoint} with payload keys: {list(payload.keys())}")
        
        # Execute the tool
        if capability.method.upper() == "GET":
            response = requests.get(capability.endpoint, params=payload, timeout=30)
        else:
            response = requests.post(capability.endpoint, json=payload, timeout=30)
        
        logger.info(f"Tool execution response status: {response.status_code}")
        response.raise_for_status()
        
        # Return the result wrapped in consistent response format
        result = response.json()
        logger.info(f"Tool execution successful, processing result for user")
        
        # Post-process the tool result with LLM interpretation
        interpreted_result = interpret_tool_result(
            tool_name=intent.primary_tool,
            tool_result=result,
            original_prompt=request.prompt,
            intent=intent
        )
        
        return JSONResponse(content={"response": interpreted_result})
        
    except Exception as e:
        logger.error(f"Single tool execution failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Single tool execution failed: {e}"}
        )


def execute_multi_step_workflow(
    intent: FlexibleIntent, 
    request: FlexibleRouteRequest,
    service_discovery
) -> JSONResponse:
    """Execute a multi-step workflow."""
    try:
        results = []
        
        for step in intent.tool_sequence:
            tool_name = step.get("tool")
            tool_params = step.get("parameters", {})
            step_description = step.get("description", f"Execute {tool_name}")
            
            logger.info(f"Executing workflow step: {step_description}")
            
            # Find server for this tool
            server = service_discovery.get_server_for_capability(tool_name)
            if not server:
                logger.warning(f"Server not found for tool: {tool_name}")
                continue
            
            # Find capability
            capability = None
            for cap in server.capabilities:
                if cap.name == tool_name:
                    capability = cap
                    break
            
            if not capability:
                logger.warning(f"Capability not found: {tool_name}")
                continue
            
            # Prepare payload
            payload = {
                **tool_params,
                "user_id": request.user_id,
                "session_id": request.session_id,
                "page": request.page,
                "tab": request.tab
            }
            
            # Execute step
            try:
                if capability.method.upper() == "GET":
                    response = requests.get(capability.endpoint, params=payload, timeout=30)
                else:
                    response = requests.post(capability.endpoint, json=payload, timeout=30)
                
                response.raise_for_status()
                step_result = response.json()
                
                results.append({
                    "step": step_description,
                    "tool": tool_name,
                    "result": step_result,
                    "status": "success"
                })
                
            except Exception as step_error:
                logger.error(f"Step failed: {step_error}")
                results.append({
                    "step": step_description,
                    "tool": tool_name,
                    "error": str(step_error),
                    "status": "failed"
                })
        
        # Return aggregated results
        return JSONResponse(content={
            "workflow_results": results,
            "total_steps": len(intent.tool_sequence),
            "successful_steps": sum(1 for r in results if r["status"] == "success"),
            "confidence": intent.confidence
        })
        
    except Exception as e:
        logger.error(f"Multi-step workflow failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Multi-step workflow failed: {e}"}
        )


def execute_complex_workflow(
    intent: FlexibleIntent, 
    request: FlexibleRouteRequest,
    service_discovery
) -> JSONResponse:
    """Execute a complex workflow with advanced orchestration."""
    try:
        # For now, treat complex workflows similar to multi-step
        # This can be expanded to include conditional logic, parallel execution, etc.
        return execute_multi_step_workflow(intent, request, service_discovery)
        
    except Exception as e:
        logger.error(f"Complex workflow failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Complex workflow failed: {e}"}
        )


@router.post("/route")
async def orchestrator_route(request: Request, body: Dict[str, Any] = Body(...)) -> JSONResponse:
    """
    Main entrypoint for orchestrator LLM routing.
    
    This endpoint now uses dynamic tool discovery and flexible routing.
    It maintains backward compatibility with the existing API.
    """
    try:
        # Convert legacy request to FlexibleRouteRequest
        flexible_request = FlexibleRouteRequest(
            prompt=body.get("prompt") or body.get("user_prompt", ""),
            user_id=body.get("user_id"),
            session_id=body.get("session_id"),
            page=body.get("page"),
            tab=body.get("tab"),
            context=body.get("context", {})
        )
        
        # Forward to flexible routing
        return await flexible_route(flexible_request)
        
    except Exception as e:
        logger.error(f"Orchestrator routing failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Orchestrator routing failed: {e}"}
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for service discovery."""
    return {"status": "healthy", "service": "orchestrator"}


@router.get("/capabilities")
async def get_capabilities():
    """Get orchestrator capabilities for service discovery."""
    return {
        "capabilities": [
            {
                "name": "flexible_routing",
                "description": "Dynamic tool discovery and intelligent routing",
                "endpoint": "http://localhost:8001/orchestrator/flexible_route",
                "method": "POST",
                "examples": ["Route user requests to appropriate tools", "Intelligent multi-step orchestration"]
            },
            {
                "name": "system_status",
                "description": "Get comprehensive system status",
                "endpoint": "http://localhost:8001/orchestrator/system_status",
                "method": "GET",
                "examples": ["Check system health", "View available services"]
            },
            {
                "name": "tool_discovery",
                "description": "Discover available tools and services",
                "endpoint": "http://localhost:8001/orchestrator/discover_tools",
                "method": "POST",
                "examples": ["List available tools", "Get tool metadata"]
            }
        ]
    }


def interpret_tool_result(
    tool_name: str,
    tool_result: Any,
    original_prompt: str,
    intent: FlexibleIntent
) -> str:
    """
    Use LLM to interpret and format tool results for user-friendly display.
    
    Args:
        tool_name: Name of the tool that was executed
        tool_result: Raw result from the tool
        original_prompt: User's original request
        intent: FlexibleIntent that was executed
        
    Returns:
        User-friendly interpretation of the tool result
    """
    try:
        # Create interpretation prompt
        interpretation_prompt = f"""
You are a business intelligence consultant presenting findings to a defense contracting professional. You just gathered information to answer their question and now need to present it clearly and professionally.

**WHAT THE USER ASKED:** {original_prompt}

**WHAT YOU FOUND:** {json.dumps(tool_result, indent=2)}

**YOUR TASK:**
Present this information as if you're having a professional conversation with a colleague. Focus on what matters most to their business needs.

**APPROACH:**
- Lead with the direct answer to their question
- Present information in a logical, easy-to-scan format
- Add brief context or insights where helpful
- Suggest relevant follow-up questions or next steps
- Keep the tone professional but conversational

**EXAMPLES OF GOOD RESPONSES:**

*For database/schema questions:*
"I found several key datasets in your system: prime awards, subawards, quarterly summaries, and various filter tables for agencies, contractors, and codes. These cover the main contracting data you'd typically need for capture analysis. Would you like me to explore any specific area?"

*For data queries:*
"Based on the latest data, here are the top 10 contractors by total obligations: [formatted results with brief insights about trends or opportunities]"

*For empty/error results:*
"I wasn't able to find data matching your criteria. This could mean [possible reasons]. Let me suggest some alternative approaches..."

**FORMATTING TIPS:**
- Use bullet points for lists
- Include totals, percentages, or context where meaningful
- Bold key findings or numbers
- Keep paragraphs short and scannable

Present your findings now:"""

        # Call LLM for interpretation
        ollama_payload = {
            "model": LLAMA3_MODEL,
            "messages": [
                {"role": "system", "content": interpretation_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower temperature for more consistent formatting
                "top_p": 0.8
            }
        }
        
        llm_response = requests.post(OLLAMA_URL, json=ollama_payload, timeout=30)
        llm_response.raise_for_status()
        interpreted_content = llm_response.json().get("message", {}).get("content", "")
        
        logger.info(f"LLM interpretation completed for tool: {tool_name}")
        return interpreted_content
        
    except Exception as e:
        logger.error(f"Tool result interpretation failed: {e}")
        # Fallback to original result if interpretation fails
        return f"I executed the {tool_name} tool successfully. Here's what I found:\n\n{json.dumps(tool_result, indent=2)}"
