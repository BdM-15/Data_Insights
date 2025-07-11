"""
Dynamic Service Discovery for MCP Server Architecture

This module replaces hard-coded tool lists with intelligent, runtime discovery
of available MCP servers and their capabilities.
"""
import asyncio
import aiohttp
import requests
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import concurrent.futures

# Configure logging
logger = logging.getLogger("service_discovery")
logger.setLevel(logging.INFO)

try:
    LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs'))
    LOG_PATH = os.path.join(LOG_DIR, 'service_discovery.log')
    os.makedirs(LOG_DIR, exist_ok=True)
    file_handler = logging.FileHandler(LOG_PATH)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    for h in logger.handlers[:]:
        logger.removeHandler(h)
    logger.addHandler(file_handler)
    print(f"[ServiceDiscovery] Logging to {LOG_PATH}")
    logger.info("[ServiceDiscovery] Logger initialized and ready.")
except Exception as log_setup_exc:
    print(f"[ServiceDiscovery] Logger setup failed: {log_setup_exc}")


@dataclass
class ServiceCapability:
    """Represents a capability provided by an MCP server."""
    name: str
    description: str
    endpoint: str
    method: str = "POST"
    parameters: Dict[str, Any] = None
    examples: List[str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.examples is None:
            self.examples = []


@dataclass 
class MCPServer:
    """Represents a discovered MCP server and its capabilities."""
    name: str
    host: str
    port: int
    base_url: str
    status: str
    capabilities: List[ServiceCapability]
    last_health_check: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ServiceDiscovery:
    """
    Dynamic service discovery for MCP servers.
    
    This class maintains a registry of available MCP servers and their capabilities,
    enabling the orchestrator to make intelligent routing decisions based on
    actual available services rather than hard-coded lists.
    """
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self.known_ports = [8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010]
        self.discovery_cache_ttl = timedelta(minutes=5)
        self.health_check_interval = timedelta(minutes=2)
        self._last_discovery = None
        
    async def discover_available_servers(self) -> Dict[str, MCPServer]:
        """
        Discover all available MCP servers by polling known ports.
        
        Returns:
            Dictionary mapping server names to MCPServer objects
        """
        if (self._last_discovery and 
            datetime.now() - self._last_discovery < self.discovery_cache_ttl):
            logger.info("Using cached server discovery results")
            return self.servers
            
        logger.info("Starting dynamic server discovery...")
        discovered_servers = {}
        
        # Simple sequential discovery - much more reliable
        for port in [8001, 8002, 8003]:  # Only check our known MCP server ports
            try:
                base_url = f"http://localhost:{port}"
                
                # Check health
                response = requests.get(f"{base_url}/health", timeout=2)
                if response.status_code == 200:
                    health_data = response.json()
                    
                    # Get capabilities  
                    caps_response = requests.get(f"{base_url}/capabilities", timeout=2)
                    capabilities = []
                    if caps_response.status_code == 200:
                        caps_data = caps_response.json()
                        for cap_info in caps_data.get("capabilities", []):
                            capability = ServiceCapability(
                                name=cap_info.get("name", "unknown"),
                                description=cap_info.get("description", ""),
                                endpoint=cap_info.get("endpoint", ""),
                                method=cap_info.get("method", "POST"),
                                parameters=cap_info.get("parameters", {}),
                                examples=cap_info.get("examples", [])
                            )
                            capabilities.append(capability)
                    
                    server = MCPServer(
                        name=health_data.get("name", f"server_{port}"),
                        host="localhost",
                        port=port,
                        base_url=base_url,
                        status="healthy",
                        capabilities=capabilities,
                        last_health_check=datetime.now(),
                        metadata=health_data
                    )
                    discovered_servers[server.name] = server
                    logger.info(f"Discovered server: {server.name} at port {port}")
                    
            except Exception as e:
                logger.debug(f"Port {port} check failed: {e}")
        
        self.servers = discovered_servers
        self._last_discovery = datetime.now()
        
        logger.info(f"Discovery complete. Found {len(discovered_servers)} active servers")
        return discovered_servers
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get a list of all available tools from discovered servers.
        
        Returns:
            List of tool dictionaries with name, description, endpoint, etc.
        """
        tools = []
        for server in self.servers.values():
            for capability in server.capabilities:
                tools.append({
                    "name": capability.name,
                    "description": capability.description,
                    "endpoint": capability.endpoint,
                    "method": capability.method,
                    "parameters": capability.parameters,
                    "examples": capability.examples,
                    "server": server.name,
                    "server_port": server.port
                })
        return tools
    
    async def get_server_for_capability(self, capability_name: str) -> Optional[MCPServer]:
        """
        Find the server that provides a specific capability.
        
        Args:
            capability_name: Name of the capability to find
            
        Returns:
            MCPServer that provides the capability, or None
        """
        for server in self.servers.values():
            for capability in server.capabilities:
                if capability.name == capability_name:
                    return server
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status and statistics.
        
        Returns:
            Dictionary with system status information
        """
        total_capabilities = sum(len(server.capabilities) for server in self.servers.values())
        healthy_servers = len([s for s in self.servers.values() if s.status == "healthy"])
        
        return {
            "total_servers": len(self.servers),
            "healthy_servers": healthy_servers,
            "total_capabilities": total_capabilities,
            "discovery_time": self._last_discovery.isoformat() if self._last_discovery else None,
            "servers": [
                {
                    "name": server.name,
                    "port": server.port,
                    "status": server.status,
                    "capabilities_count": len(server.capabilities)
                }
                for server in self.servers.values()
            ]
        }


# Global service discovery instance
_service_discovery_instance = None

def get_service_discovery() -> ServiceDiscovery:
    """
    Get the global service discovery instance.
    
    Returns:
        ServiceDiscovery instance
    """
    global _service_discovery_instance
    if _service_discovery_instance is None:
        _service_discovery_instance = ServiceDiscovery()
    return _service_discovery_instance
