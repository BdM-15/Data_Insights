"""
Data Insights Python MCP Servers Launcher

Pure Python MCP SDK implementation replacing the FastMCP hybrid stack.
Provides automatic tool discovery, Ollama integration, and production-ready MCP server management.

Architecture:
- Python MCP SDK (official implementation)
- stdio transport for reliable client-server communication
- Automatic server discovery and health monitoring
- Future-proof tool registration system
"""

import os
import sys
import subprocess
import time
import logging
import importlib
import pkgutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from colorama import Fore, Style, init
import argparse

# Initialize colorama for colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mcp_server_activity.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add src to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def check_mcp_sdk() -> bool:
    """
    Check Python MCP SDK availability and version.
    
    Returns:
        bool: True if MCP SDK is available and compatible
    """
    try:
        import mcp
        version = getattr(mcp, '__version__', 'unknown')
        print(f"{Fore.GREEN}✅ Python MCP SDK available (version: {version}){Style.RESET_ALL}")
        
        # Check for required components
        required_modules = ['mcp.server', 'mcp.client', 'mcp.types']
        for module in required_modules:
            try:
                importlib.import_module(module)
                print(f"{Fore.GREEN}  ✓ {module} available{Style.RESET_ALL}")
            except ImportError as e:
                print(f"{Fore.RED}  ✗ {module} missing: {e}{Style.RESET_ALL}")
                return False
        
        return True
        
    except ImportError as e:
        print(f"{Fore.RED}❌ Python MCP SDK not found: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Install with: pip install mcp>=1.0.0{Style.RESET_ALL}")
        return False

def check_database_connectivity() -> bool:
    """
    Test database connectivity using config.py settings.
    
    Returns:
        bool: True if database is accessible
    """
    try:
        from config import get_db_config
        import asyncpg
        import asyncio
        
        async def test_connection():
            db_config = get_db_config()
            conn_params = {
                "host": db_config["PG_HOST"],
                "port": int(db_config["PG_PORT"]),
                "database": db_config["PG_DBNAME"],
                "user": db_config["PG_USER"],
                "password": db_config["PG_PASSWORD"]
            }
            
            conn = await asyncpg.connect(**conn_params)
            version_result = await conn.fetchrow("SELECT version();")
            await conn.close()
            return version_result
        
        result = asyncio.run(test_connection())
        print(f"{Fore.GREEN}✅ Database connectivity verified{Style.RESET_ALL}")
        print(f"{Fore.GREEN}  📊 PostgreSQL: {result['version'][:50]}...{Style.RESET_ALL}")
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ Database connectivity failed: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Check database configuration in config.py{Style.RESET_ALL}")
        return False

def check_ollama() -> bool:
    """
    Check if Ollama LLM service is running and available.
    
    Returns:
        bool: True if Ollama is running with models available
    """
    try:
        print(f"{Fore.CYAN}🧠 Checking Ollama LLM service...{Style.RESET_ALL}")
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"{Fore.GREEN}✅ Ollama LLM service is running with {len(models)} models{Style.RESET_ALL}")
            
            # Look for optimized models
            data_insights_model = next((m for m in models if 'data_insights' in m.get('name', '')), None)
            if data_insights_model:
                print(f"{Fore.GREEN}  🎯 Data Insights optimized model: {data_insights_model['name']}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}  ⚠️  Data Insights optimized model not found - using default model{Style.RESET_ALL}")
            
            return True
        else:
            print(f"{Fore.YELLOW}⚠️  Ollama responding with status {response.status_code}{Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Ollama LLM service is not running: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Please start Ollama: 'ollama serve'{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}💡 Then load your model: 'ollama run data_insights_optimized' or 'ollama run llama2'{Style.RESET_ALL}")
        return False

def discover_mcp_servers() -> List[Dict[str, Any]]:
    """
    Automatically discover available MCP servers in the project.
    
    Returns:
        List[Dict]: List of discovered server configurations
    """
    servers = []
    mcp_servers_dir = project_root / "src" / "backend" / "ai" / "mcp_servers"
    
    if not mcp_servers_dir.exists():
        print(f"{Fore.YELLOW}⚠️  MCP servers directory not found: {mcp_servers_dir}{Style.RESET_ALL}")
        return servers
    
    print(f"{Fore.CYAN}🔍 Discovering MCP servers in {mcp_servers_dir}...{Style.RESET_ALL}")
    
    # Look for Python MCP server files
    for py_file in mcp_servers_dir.rglob("*_server.py"):
        if py_file.name.startswith("python_mcp_"):
            try:
                # Extract server information
                server_name = py_file.stem.replace("python_mcp_", "").replace("_server", "")
                
                # Handle nested server structure (e.g., data_insights_database/python_mcp_database_server.py)
                relative_path = py_file.relative_to(mcp_servers_dir)
                if len(relative_path.parts) > 1:
                    # Server in subfolder
                    module_path = f"backend.ai.mcp_servers.{relative_path.parts[0]}.{py_file.stem}"
                else:
                    # Server in root mcp_servers directory
                    module_path = f"backend.ai.mcp_servers.{py_file.stem}"
                
                servers.append({
                    "name": server_name,
                    "module": module_path,
                    "file_path": str(py_file),
                    "transport": "stdio",
                    "type": "python_mcp"
                })
                print(f"{Fore.GREEN}  ✓ Found {server_name} server: {relative_path}{Style.RESET_ALL}")
                
            except Exception as e:
                print(f"{Fore.YELLOW}  ⚠️  Error processing {py_file.name}: {e}{Style.RESET_ALL}")
    
    return servers

def validate_server(server_config: Dict[str, Any]) -> bool:
    """
    Validate that a server module can be imported and has required components.
    
    Args:
        server_config: Server configuration dictionary
        
    Returns:
        bool: True if server is valid and can be loaded
    """
    try:
        module = importlib.import_module(server_config["module"])
        
        # Check for required server components
        required_attrs = ["server", "main"]
        for attr in required_attrs:
            if not hasattr(module, attr):
                print(f"{Fore.RED}  ✗ {server_config['name']}: missing {attr}{Style.RESET_ALL}")
                return False
        
        print(f"{Fore.GREEN}  ✓ {server_config['name']}: validation passed{Style.RESET_ALL}")
        return True
        
    except ImportError as e:
        print(f"{Fore.RED}  ✗ {server_config['name']}: import failed - {e}{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}  ✗ {server_config['name']}: validation error - {e}{Style.RESET_ALL}")
        return False

def get_server_tools(server_config: Dict[str, Any]) -> List[str]:
    """
    Get list of available tools from a server module.
    
    Args:
        server_config: Server configuration dictionary
        
    Returns:
        List[str]: List of tool names
    """
    try:
        module = importlib.import_module(server_config["module"])
        server = getattr(module, "server", None)
        
        if server and hasattr(server, "_list_tools_handler"):
            # For Python MCP SDK servers
            import asyncio
            tools = asyncio.run(server._list_tools_handler())
            return [tool.name for tool in tools]
        
        return []
        
    except Exception as e:
        logger.debug(f"Could not get tools for {server_config['name']}: {e}")
        return []

def start_python_mcp_servers(servers: Optional[List[Dict[str, Any]]] = None):
    """
    Start Python MCP SDK servers with comprehensive status reporting.
    
    Args:
        servers: Optional list of server configurations. If None, auto-discover.
    """
    print(f"{Fore.CYAN}🚀 Starting Python MCP SDK servers...{Style.RESET_ALL}")
    
    # Auto-discover servers if not provided
    if servers is None:
        servers = discover_mcp_servers()
    
    if not servers:
        print(f"{Fore.YELLOW}⚠️  No MCP servers found for startup{Style.RESET_ALL}")
        return
    
    # Validate servers
    valid_servers = []
    print(f"{Fore.CYAN}🔍 Validating discovered servers...{Style.RESET_ALL}")
    for server in servers:
        if validate_server(server):
            valid_servers.append(server)
    
    if not valid_servers:
        print(f"{Fore.RED}❌ No valid MCP servers found{Style.RESET_ALL}")
        return
    
    # Display server information
    print(f"\n{Fore.GREEN}✅ Python MCP SDK servers ready for client connections:{Style.RESET_ALL}")
    for server in valid_servers:
        print(f"{Fore.CYAN}📍 {server['name'].title()} Server:{Style.RESET_ALL}")
        print(f"  🔗 Transport: {server['transport']}")
        print(f"  📁 Module: {server['module']}")
        print(f"  🚀 Command: python -m {server['module']}")
        print()
    
    # Show connection information
    print(f"{Fore.GREEN}🎯 Client Connection Examples:{Style.RESET_ALL}")
    for server in valid_servers:
        print(f"  python -m {server['module']}")
    
    print(f"\n{Fore.GREEN}🎯 Python MCP SDK Architecture Benefits:{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✓ Pure Python implementation (no TypeScript hybrid){Style.RESET_ALL}")
    print(f"{Fore.GREEN}✓ Official MCP SDK support and documentation{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✓ Better async/await handling and stability{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✓ Resolves 'Event loop is closed' errors{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✓ Future-proof tool discovery and registration{Style.RESET_ALL}")

def run_health_checks() -> bool:
    """
    Run comprehensive health checks for the MCP environment.
    
    Returns:
        bool: True if all health checks pass
    """
    print(f"{Fore.CYAN}🏥 Running MCP environment health checks...{Style.RESET_ALL}")
    
    checks = [
        ("Python MCP SDK", check_mcp_sdk),
        ("Database Connectivity", check_database_connectivity),
        ("Ollama LLM Service", check_ollama)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n{Fore.CYAN}Checking {check_name}...{Style.RESET_ALL}")
        if not check_func():
            all_passed = False
    
    print(f"\n{Fore.CYAN}🔍 Health check summary:{Style.RESET_ALL}")
    if all_passed:
        print(f"{Fore.GREEN}✅ All health checks passed - system ready{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ Some health checks failed - see details above{Style.RESET_ALL}")
    
    return all_passed

def main():
    """Main entry point for the Python MCP servers launcher."""
    parser = argparse.ArgumentParser(
        description='Data Insights Python MCP Servers Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python python_mcp_servers_launcher.py                    # Start all servers
  python python_mcp_servers_launcher.py --health-check     # Run health checks only
  python python_mcp_servers_launcher.py --discover         # Discover servers only
        """
    )
    
    parser.add_argument('--health-check', action='store_true',
                        help='Run health checks only without starting servers')
    parser.add_argument('--discover', action='store_true',
                        help='Discover and validate servers only')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print(f"{Fore.CYAN}🚀 Data Insights Python MCP Servers Launcher{Style.RESET_ALL}")
    print(f"{Fore.CYAN}📡 Pure Python MCP SDK implementation{Style.RESET_ALL}\n")
    
    # Run health checks
    if not run_health_checks():
        if not args.health_check:
            print(f"\n{Fore.RED}❌ Health checks failed. Please fix issues before starting servers.{Style.RESET_ALL}")
            sys.exit(1)
        else:
            sys.exit(1)
    
    if args.health_check:
        print(f"\n{Fore.GREEN}🎉 Health checks completed successfully{Style.RESET_ALL}")
        return
    
    # Discover servers
    servers = discover_mcp_servers()
    
    if args.discover:
        print(f"\n{Fore.GREEN}🔍 Server discovery completed{Style.RESET_ALL}")
        return
    
    # Start servers
    start_python_mcp_servers(servers)
    
    print(f"\n{Fore.GREEN}🔄 Python MCP servers are ready for client connections{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💡 Use the connection examples above to connect MCP clients{Style.RESET_ALL}")
    print(f"{Fore.CYAN}📝 Server activity logged to: logs/mcp_server_activity.log{Style.RESET_ALL}")



if __name__ == "__main__":
    main()
