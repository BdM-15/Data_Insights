"""
MCP Servers Launcher - Enhanced

Comprehensive MCP server management with:
- Intelligent server discovery and health monitoring
- Ollama LLM integration and status checking
- Color-coded logging for better readability
- User-friendly status reporting
- Automatic service management

Designed for seamless operation with Data Insights AI chat system.
"""

import os
import sys
import subprocess
import logging
import time
import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Color codes for console output
class Colors:
    """ANSI color codes for enhanced console output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Custom formatter with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""
    
    COLORS = {
        'DEBUG': Colors.OKBLUE,
        'INFO': Colors.OKGREEN,
        'WARNING': Colors.WARNING,
        'ERROR': Colors.FAIL,
        'CRITICAL': Colors.FAIL + Colors.BOLD
    }
    
    def format(self, record):
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Colors.ENDC}"
        
        return super().format(record)

# Configure enhanced logging
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
))

file_handler = logging.FileHandler('logs/mcp_server_activity.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

class MCPServerLauncher:
    """
    Enhanced MCP server launcher with comprehensive service management.
    
    Features:
    - MCP server discovery and lifecycle management
    - Ollama LLM service integration and monitoring
    - Color-coded status reporting
    - Intelligent health monitoring with auto-restart
    - User-friendly progress indicators
    """
    
    def __init__(self):
        """Initialize the launcher with enhanced configuration."""
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.health_status: Dict[str, bool] = {}
        
        # Server configurations - Only define the primary servers here
        self.server_configs = {
            "database": {
                "name": "Data Insights Database Server",
                "path": "fastmcp_database_server_fixed.py",
                "description": "PostgreSQL database access for contract data",
                "icon": "🗄️"
            }
        }
        
        # Ollama configuration
        self.ollama_url = "http://localhost:11434"
        self.primary_model = "data_insights_optimized:latest"  # Primary orchestrator agent
        self.discovered_models = []  # Auto-discovered models
        self.discovered_servers = {}  # Auto-discovered MCP servers
    
    def print_header(self):
        """Print a welcome header."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}  🚀 Data Insights MCP Server Launcher  🚀{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Initializing AI-powered contract intelligence system...{Colors.ENDC}\n")
    
    def discover_mcp_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        Auto-discover MCP servers in the project (future-proof).
        
        Returns:
            Dictionary of discovered server configurations
        """
        discovered = {}
        
        logger.info("🔍 Auto-discovering MCP servers...")
        
        # Only search in project directories, not in site-packages or venv
        search_dirs = [
            project_root,
            project_root / "src" / "backend" / "ai" / "mcp_servers",
            project_root / "src" / "backend" / "mcp_servers",
            project_root / "mcp_servers"
        ]
        
        # Only look for files that are clearly MCP servers for this project
        mcp_server_patterns = [
            "fastmcp_*.py",
            "*_mcp_server.py",
            "*_intelligence_server.py",
            "*_database_server.py",
            "*_capture_server.py"
        ]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
                
            for pattern in mcp_server_patterns:
                for server_file in search_dir.glob(pattern):
                    # Only process files in the project directory (not in venv/site-packages)
                    if not server_file.is_file() or "site-packages" in str(server_file) or "venv" in str(server_file):
                        continue
                        
                    server_name = server_file.stem
                    
                    # Skip if already found (avoid duplicates)
                    if server_name in discovered:
                        continue
                    
                    # Auto-determine server type and icon from filename
                    icon = "🔧"  # Default icon
                    description = "MCP server"
                    
                    if "database" in server_name.lower():
                        icon = "🗄️"
                        description = "Database access server"
                    elif "capture" in server_name.lower() or "intelligence" in server_name.lower():
                        icon = "🎯"
                        description = "Intelligence server"
                    elif "web" in server_name.lower():
                        icon = "🌐"
                        description = "Web server"
                    elif "document" in server_name.lower():
                        icon = "📄"
                        description = "Document processing server"
                    elif "visualization" in server_name.lower():
                        icon = "📊"
                        description = "Visualization server"
                    
                    discovered[server_name] = {
                        "name": server_name.replace("_", " ").title(),
                        "path": str(server_file.relative_to(project_root)),
                        "description": description,
                        "icon": icon,
                        "discovered": True
                    }
                    
                    logger.info(f"   {Colors.OKCYAN}🔍{Colors.ENDC} Found {icon} {server_name}")
        
        return discovered
        
        logger.info("🔍 Auto-discovering MCP servers...")
        
        # Search in project root first
        for server_file in specific_servers:
            server_path = project_root / server_file
            if server_path.exists():
                server_name = server_path.stem
                
                # Skip if already in manual config
                if server_name in self.server_configs:
                    continue
                
                # Skip all database servers since we have one manually configured
                if "database" in server_name.lower():
                    continue
                
                # Determine server type and icon from filename
                icon = "🔧"  # Default icon
                description = "MCP server"
                
                if "database" in server_name.lower():
                    icon = "🗄️"
                    description = "Database access server"
                elif "capture" in server_name.lower():
                    icon = "🎯"
                    description = "Capture intelligence server"
                elif "web" in server_name.lower():
                    icon = "🌐"
                    description = "Web intelligence server"
                elif "document" in server_name.lower():
                    icon = "📄"
                    description = "Document processing server"
                elif "visualization" in server_name.lower():
                    icon = "📊"
                    description = "Visualization server"
                
                discovered[server_name] = {
                    "name": server_name.replace("_", " ").title(),
                    "path": server_file,
                    "description": description,
                    "icon": icon,
                    "discovered": True
                }
                
                logger.info(f"   {Colors.OKCYAN}🔍{Colors.ENDC} Found {icon} {server_name}")
        
        # Also check the MCP servers directory if it exists
        mcp_servers_dir = project_root / "src" / "backend" / "ai" / "mcp_servers"
        if mcp_servers_dir.exists():
            for subdir in mcp_servers_dir.iterdir():
                if subdir.is_dir():
                    # Look for the main server file in each subdirectory
                    for server_file in subdir.glob("*_server.py"):
                        if server_file.is_file():
                            server_name = server_file.stem
                            
                            # Skip if already found or in manual config
                            if server_name in discovered or server_name in self.server_configs:
                                continue
                            
                            # Skip all database servers since we have one manually configured
                            if "database" in server_name.lower():
                                continue
                            
                            # Determine server type
                            icon = "🔧"
                            description = "MCP server"
                            
                            if "database" in server_name.lower():
                                icon = "�️"
                                description = "Database access server"
                            elif "capture" in server_name.lower():
                                icon = "🎯"
                                description = "Capture intelligence server"
                            elif "web" in server_name.lower():
                                icon = "🌐"
                                description = "Web intelligence server"
                            elif "document" in server_name.lower():
                                icon = "📄"
                                description = "Document processing server"
                            elif "visualization" in server_name.lower():
                                icon = "📊"
                                description = "Visualization server"
                            
                            discovered[server_name] = {
                                "name": server_name.replace("_", " ").title(),
                                "path": str(server_file.relative_to(project_root)),
                                "description": description,
                                "icon": icon,
                                "discovered": True
                            }
                            
                            logger.info(f"   {Colors.OKCYAN}🔍{Colors.ENDC} Found {icon} {server_name}")
        
        return discovered
    
    def discover_ollama_models(self) -> List[str]:
        """
        Auto-discover available Ollama models.
        
        Returns:
            List of available model names
        """
        models = []
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                models = [model['name'] for model in models_data.get('models', [])]
                
                logger.info(f"🔍 Discovered {len(models)} Ollama models:")
                for model in models:
                    # Categorize models by type
                    model_icon = "🤖"
                    if "data_insights" in model:
                        model_icon = "🎯"  # Custom trained model
                    elif "llama" in model:
                        model_icon = "🦙"
                    elif "mistral" in model:
                        model_icon = "🌟"
                    elif "code" in model:
                        model_icon = "💻"
                    
                    primary_indicator = " (Primary)" if model == self.primary_model else ""
                    logger.info(f"   {Colors.OKGREEN}✓{Colors.ENDC} {model_icon} {model}{primary_indicator}")
                    
        except requests.exceptions.RequestException:
            logger.warning(f"   {Colors.WARNING}⚠{Colors.ENDC} Could not discover Ollama models")
        
        return models
    
    def check_ollama_service(self) -> bool:
        """Check if Ollama service is running."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def check_ollama_service_with_logging(self) -> bool:
        """Check if Ollama service is running with detailed logging."""
        logger.info("🤖 Checking Ollama LLM service...")
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"   {Colors.OKGREEN}✓{Colors.ENDC} Ollama service is running")
                return True
            else:
                logger.warning(f"   {Colors.WARNING}⚠{Colors.ENDC} Ollama service responded with status {response.status_code}")
                return False
        except requests.exceptions.RequestException:
            logger.warning(f"   {Colors.WARNING}⚠{Colors.ENDC} Ollama service is not running")
            return False
    
    def check_ollama_models(self) -> bool:
        """Check and validate discovered Ollama models."""
        logger.info("🔍 Checking available LLM models...")
        
        # Discover all available models
        self.discovered_models = self.discover_ollama_models()
        
        if not self.discovered_models:
            logger.error(f"   {Colors.FAIL}✗{Colors.ENDC} No Ollama models found")
            return False
        
        # Check if primary model is available
        if self.primary_model not in self.discovered_models:
            logger.warning(f"   {Colors.WARNING}⚠{Colors.ENDC} Primary model '{self.primary_model}' not found")
            logger.info(f"   {Colors.OKCYAN}💡{Colors.ENDC} Available models: {', '.join(self.discovered_models)}")
            return False
        
        logger.info(f"   {Colors.OKGREEN}✓{Colors.ENDC} Primary model '{self.primary_model}' is available")
        return True
    
    def start_ollama_if_needed(self) -> bool:
        """Start Ollama service if it's not running."""
        if self.check_ollama_service_with_logging():
            return True
        
        logger.info("🔧 Starting Ollama service...")
        
        try:
            # Try to start Ollama in the background
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            
            # Wait a moment for service to start
            time.sleep(3)
            
            # Check if it's running now
            if self.check_ollama_service():
                logger.info(f"   {Colors.OKGREEN}✓{Colors.ENDC} Ollama service started successfully")
                return True
            else:
                logger.warning(f"   {Colors.WARNING}⚠{Colors.ENDC} Ollama service failed to start")
                return False
                
        except FileNotFoundError:
            logger.error(f"   {Colors.FAIL}✗{Colors.ENDC} Ollama is not installed. Please install from https://ollama.ai/")
            return False
        except Exception as e:
            logger.error(f"   {Colors.FAIL}✗{Colors.ENDC} Failed to start Ollama: {e}")
            return False
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        logger.info("📋 Checking system prerequisites...")
        
        # Check MCP SDK
        try:
            import mcp
            from mcp.server.fastmcp import FastMCP
            logger.info(f"   {Colors.OKGREEN}✓{Colors.ENDC} MCP SDK is available")
        except ImportError:
            logger.error(f"   {Colors.FAIL}✗{Colors.ENDC} MCP SDK not available. Install with: pip install mcp>=1.0.0")
            return False
        
        # Check database connectivity
        try:
            from config import get_db_config
            db_config = get_db_config()
            logger.info(f"   {Colors.OKGREEN}✓{Colors.ENDC} Database configuration loaded")
        except Exception as e:
            logger.error(f"   {Colors.FAIL}✗{Colors.ENDC} Database configuration error: {e}")
            return False
        
        # Auto-discover MCP servers (future-proof)
        self.discovered_servers = self.discover_mcp_servers()
        
        # Use discovered servers as the active configuration
        self.server_configs = self.discovered_servers
        
        # Check if we found any servers
        if not self.server_configs:
            logger.warning(f"   {Colors.WARNING}⚠{Colors.ENDC} No MCP servers discovered")
            return False
        
        # Check server files exist
        for server_name, config in self.server_configs.items():
            server_path = project_root / config["path"]
            if not server_path.exists():
                logger.error(f"   {Colors.FAIL}✗{Colors.ENDC} Server file not found: {server_path}")
                return False
            else:
                logger.info(f"   {Colors.OKGREEN}✓{Colors.ENDC} {config['icon']} {config['name']} found")
        
        # Check Ollama service
        if not self.start_ollama_if_needed():
            logger.warning(f"   {Colors.WARNING}⚠{Colors.ENDC} Ollama service issues - AI features may be limited")
        
        # Check Ollama models
        if not self.check_ollama_models():
            logger.warning(f"   {Colors.WARNING}⚠{Colors.ENDC} Primary model validation failed - AI features may be limited")
        
        return True
    
    def start_server(self, server_name: str) -> bool:
        """
        Start a specific MCP server with enhanced monitoring.
        
        Args:
            server_name: Name of the server to start
            
        Returns:
            True if server started successfully
        """
        if server_name not in self.server_configs:
            logger.error(f"❌ Unknown server: {server_name}")
            return False
        
        config = self.server_configs[server_name]
        server_path = project_root / config["path"]
        
        logger.info(f"🚀 Starting {config['icon']} {config['name']}...")
        
        try:
            # Start the server process
            process = subprocess.Popen(
                [sys.executable, str(server_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(project_root)
            )
            
            # Brief pause to check if process started successfully
            time.sleep(0.5)
            if process.poll() is not None:
                # Process died immediately
                stdout, stderr = process.communicate()
                logger.error(f"   {Colors.FAIL}✗{Colors.ENDC} Server failed to start")
                if stderr:
                    logger.error(f"   {Colors.FAIL}Error output:{Colors.ENDC} {stderr.decode()}")
                return False
            
            self.processes[server_name] = process
            self.health_status[server_name] = True
            
            logger.info(f"   {Colors.OKGREEN}✓{Colors.ENDC} Server running (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"   {Colors.FAIL}✗{Colors.ENDC} Failed to start server: {e}")
            self.health_status[server_name] = False
            return False
    
    def stop_server(self, server_name: str) -> bool:
        """
        Stop a specific MCP server gracefully.
        
        Args:
            server_name: Name of the server to stop
            
        Returns:
            True if server stopped successfully
        """
        if server_name not in self.processes:
            logger.info(f"🛑 Server {server_name} is not running")
            return True
        
        config = self.server_configs[server_name]
        process = self.processes[server_name]
        
        logger.info(f"🛑 Stopping {config['icon']} {config['name']}...")
        
        try:
            # Terminate the process
            process.terminate()
            
            # Wait for clean shutdown
            try:
                process.wait(timeout=5)
                logger.info(f"   {Colors.OKGREEN}✓{Colors.ENDC} Server stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if necessary
                process.kill()
                process.wait()
                logger.warning(f"   {Colors.WARNING}⚠{Colors.ENDC} Server force-killed (unresponsive)")
            
            # Clean up
            del self.processes[server_name]
            self.health_status[server_name] = False
            
            return True
            
        except Exception as e:
            logger.error(f"   {Colors.FAIL}✗{Colors.ENDC} Failed to stop server: {e}")
            return False
    
    def start_all_servers(self) -> bool:
        """
        Start all configured servers.
        
        Returns:
            True if all servers started successfully
        """
        logger.info("🚀 Starting all MCP servers...")
        
        success = True
        for server_name in self.server_configs:
            if not self.start_server(server_name):
                success = False
        
        if success:
            logger.info(f"   {Colors.OKGREEN}✓{Colors.ENDC} All servers started successfully")
        else:
            logger.warning(f"   {Colors.WARNING}⚠{Colors.ENDC} Some servers failed to start")
        
        return success
    
    def stop_all_servers(self) -> bool:
        """
        Stop all running servers.
        
        Returns:
            True if all servers stopped successfully
        """
        logger.info("🛑 Stopping all MCP servers...")
        
        success = True
        for server_name in list(self.processes.keys()):
            if not self.stop_server(server_name):
                success = False
        
        if success:
            logger.info(f"   {Colors.OKGREEN}✓{Colors.ENDC} All servers stopped successfully")
        else:
            logger.warning(f"   {Colors.WARNING}⚠{Colors.ENDC} Some servers failed to stop cleanly")
        
        return success
    
    def check_server_health(self, server_name: str) -> bool:
        """
        Check if a server is healthy.
        
        Args:
            server_name: Name of the server to check
            
        Returns:
            True if server is healthy
        """
        if server_name not in self.processes:
            return False
        
        process = self.processes[server_name]
        
        # Check if process is still running
        if process.poll() is not None:
            logger.warning(f"   {Colors.WARNING}⚠{Colors.ENDC} Server {server_name} process has terminated")
            self.health_status[server_name] = False
            return False
        
        # Additional health checks could go here
        # For now, just check if process is running
        self.health_status[server_name] = True
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of all servers.
        
        Returns:
            Dictionary with detailed server status information
        """
        # Update health status
        for server_name in self.processes:
            self.check_server_health(server_name)
        
        status = {
            "servers": {},
            "total_servers": len(self.server_configs),
            "running_servers": len(self.processes),
            "healthy_servers": sum(1 for health in self.health_status.values() if health),
            "discovered_models": len(self.discovered_models),
            "primary_model": self.primary_model
        }
        
        for server_name, config in self.server_configs.items():
            is_running = server_name in self.processes
            is_healthy = self.health_status.get(server_name, False) if is_running else False
            
            status["servers"][server_name] = {
                "name": config["name"],
                "description": config["description"],
                "icon": config["icon"],
                "running": is_running,
                "healthy": is_healthy,
                "pid": self.processes[server_name].pid if is_running else None
            }
        
        return status
    
    def print_status(self):
        """Print a comprehensive status report."""
        status = self.get_status()
        
        print(f"\n{Colors.OKCYAN}📊 System Status Report{Colors.ENDC}")
        print(f"{Colors.OKCYAN}{'─' * 25}{Colors.ENDC}")
        
        # MCP Servers Status
        print(f"{Colors.OKBLUE}MCP Servers:{Colors.ENDC}")
        for server_name, info in status["servers"].items():
            icon = info["icon"]
            name = info["name"]
            
            if info["running"] and info["healthy"]:
                status_icon = f"{Colors.OKGREEN}🟢{Colors.ENDC}"
                status_text = f"{Colors.OKGREEN}Running{Colors.ENDC}"
                pid_text = f"(PID: {info['pid']})"
            elif info["running"]:
                status_icon = f"{Colors.WARNING}🟡{Colors.ENDC}"
                status_text = f"{Colors.WARNING}Unhealthy{Colors.ENDC}"
                pid_text = f"(PID: {info['pid']})"
            else:
                status_icon = f"{Colors.FAIL}🔴{Colors.ENDC}"
                status_text = f"{Colors.FAIL}Stopped{Colors.ENDC}"
                pid_text = ""
            
            discovered_text = ""
            print(f"  {status_icon} {icon} {name}: {status_text} {pid_text}{discovered_text}")
        
        print(f"\n{Colors.OKBLUE}Overall: {status['healthy_servers']}/{status['total_servers']} servers healthy{Colors.ENDC}")
        
        # Ollama Service and Models Status
        print(f"{Colors.OKBLUE}AI Services:{Colors.ENDC}")
        if self.check_ollama_service():
            print(f"  {Colors.OKGREEN}🟢{Colors.ENDC} 🤖 Ollama LLM Service: {Colors.OKGREEN}Running{Colors.ENDC}")
            
            # Show available models
            if self.discovered_models:
                print(f"  {Colors.OKCYAN}Available Models ({len(self.discovered_models)}):{Colors.ENDC}")
                for model in self.discovered_models:
                    model_icon = "🤖"
                    if "data_insights" in model:
                        model_icon = "🎯"
                    elif "llama" in model:
                        model_icon = "🦙"
                    elif "mistral" in model:
                        model_icon = "🌟"
                    elif "code" in model:
                        model_icon = "💻"
                    
                    primary_indicator = f" {Colors.OKGREEN}(Primary){Colors.ENDC}" if model == self.primary_model else ""
                    print(f"    {model_icon} {model}{primary_indicator}")
        else:
            print(f"  {Colors.FAIL}🔴{Colors.ENDC} 🤖 Ollama LLM Service: {Colors.FAIL}Stopped{Colors.ENDC}")
        
        print()
    
    def monitor_health(self):
        """Monitor server health with enhanced reporting."""
        logger.info("🔍 Starting health monitoring...")
        logger.info(f"   {Colors.OKCYAN}💡{Colors.ENDC} Press Ctrl+C to stop monitoring")
        
        monitor_count = 0
        while True:
            try:
                # Check server health
                unhealthy_servers = []
                for server_name in list(self.processes.keys()):
                    if not self.check_server_health(server_name):
                        unhealthy_servers.append(server_name)
                
                # Restart unhealthy servers
                if unhealthy_servers:
                    logger.warning(f"🔄 Restarting {len(unhealthy_servers)} unhealthy server(s)...")
                    for server_name in unhealthy_servers:
                        self.stop_server(server_name)
                        time.sleep(1)
                        self.start_server(server_name)
                
                # Print status every 10 cycles (100 seconds)
                monitor_count += 1
                if monitor_count % 10 == 0:
                    self.print_status()
                    monitor_count = 0
                
                time.sleep(10)  # Check every 10 seconds
                
            except KeyboardInterrupt:
                logger.info("🛑 Health monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"   {Colors.FAIL}✗{Colors.ENDC} Error in health monitoring: {e}")
                time.sleep(5)

def main():
    """Main entry point with enhanced user experience."""
    launcher = MCPServerLauncher()
    
    # Print welcome header
    launcher.print_header()
    
    try:
        # Check prerequisites
        if not launcher.check_prerequisites():
            logger.error(f"{Colors.FAIL}❌ Prerequisites check failed. Please fix the issues above.{Colors.ENDC}")
            return 1
        
        print(f"{Colors.OKGREEN}✅ All prerequisites satisfied{Colors.ENDC}\n")
        
        # Start servers
        if not launcher.start_all_servers():
            logger.error(f"{Colors.FAIL}❌ Failed to start all servers. Check logs for details.{Colors.ENDC}")
            return 1
        
        # Print initial status
        launcher.print_status()
        
        # Monitor health
        launcher.monitor_health()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}🛑 Shutdown requested by user...{Colors.ENDC}")
    except Exception as e:
        logger.error(f"{Colors.FAIL}💥 Unexpected error: {e}{Colors.ENDC}")
        return 1
    finally:
        # Clean shutdown
        print(f"{Colors.OKCYAN}🔄 Shutting down services...{Colors.ENDC}")
        launcher.stop_all_servers()
        print(f"{Colors.OKGREEN}✅ Shutdown complete{Colors.ENDC}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
