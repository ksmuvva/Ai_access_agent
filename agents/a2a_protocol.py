"""
A2A Protocol Implementation for Google ADK
Agent-to-Agent communication protocol for distributed accessibility testing
Using official A2A SDK for protocol compliance
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import uuid
import logging

# Official A2A SDK imports
try:
    from a2a_sdk import A2AClient, A2AServer as OfficialA2AServer, AgentCard
    from a2a_sdk.exceptions import A2AException
    A2A_SDK_AVAILABLE = True
except ImportError:
    # Fallback for development if official SDK not available
    A2A_SDK_AVAILABLE = False
    logging.warning("Official A2A SDK not available, using fallback implementation")

from .agent_card import AccessibilityAgentCard
from .a2a_server import A2AServer

logger = logging.getLogger(__name__)


@dataclass
class RemoteAgent:
    """Represents a remote accessibility testing agent"""
    name: str
    endpoint: str
    agent_type: str
    capabilities: Dict[str, Any]
    protocol_version: str = "A2A-1.0"
    last_seen: Optional[datetime] = None


@dataclass 
class A2ARequest:
    """A2A protocol request structure"""
    request_id: str
    action: str
    payload: Dict[str, Any]
    source_agent: str
    target_agent: str
    timestamp: datetime


@dataclass
class A2AResponse:
    """A2A protocol response structure"""
    request_id: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None


class A2AProtocol:
    """
    Enhanced A2A Protocol Implementation with official SDK integration
    Provides agent discovery, communication, and coordination capabilities
    """
    
    def __init__(self, server_host: str = "localhost", server_port: int = 8080):
        self.server_host = server_host
        self.server_port = server_port
        self.server_url = f"http://{server_host}:{server_port}"
        
        # A2A Server for hosting local agents
        self.local_server = A2AServer(host=server_host, port=server_port)
        self.is_server_running = False
        
        # Official A2A client if available
        if A2A_SDK_AVAILABLE:
            self.client = A2AClient(base_url=self.server_url)
        else:
            self.client = None
            
        # Agent registry
        self.known_agents: Dict[str, RemoteAgent] = {}
        self.agent_cards: Dict[str, AccessibilityAgentCard] = {}
        
    async def start_server(self, agents: List[Any] = None, agent_cards: List[AccessibilityAgentCard] = None):
        """
        Start local A2A server with registered agents
        
        Args:
            agents: List of agent instances to register
            agent_cards: Corresponding agent cards for capabilities
        """
        try:
            if agents and agent_cards:
                for agent, card in zip(agents, agent_cards):
                    self.local_server.register_agent(agent, card)
                    
            await self.local_server.start()
            self.is_server_running = True
            
            logger.info(f"A2A Protocol server started on {self.server_host}:{self.server_port}")
            
        except Exception as e:
            logger.error(f"Failed to start A2A server: {e}")
            raise
    
    async def stop_server(self):
        """Stop the local A2A server"""
        if self.is_server_running:
            await self.local_server.stop()
            self.is_server_running = False
            logger.info("A2A Protocol server stopped")
    
    async def discover_agents(
        self, 
        agent_type: str = "accessibility_tester",
        capabilities: List[str] = None,
        discovery_endpoints: List[str] = None
    ) -> List[RemoteAgent]:
        """
        Discover remote accessibility agents via A2A protocol
        
        Args:
            agent_type: Type of agents to discover
            capabilities: Required capabilities to filter by
            discovery_endpoints: Additional endpoints to search
            
        Returns:
            List of discovered remote agents
        """
        discovered_agents = []
        
        # Default discovery endpoints
        if discovery_endpoints is None:
            discovery_endpoints = [
                "http://localhost:8080",
                "http://localhost:8081", 
                "http://localhost:8082"
            ]
            
        for endpoint in discovery_endpoints:
            try:
                # Try to get agent list from endpoint
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{endpoint}/a2a/agents") as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for agent_info in data.get("agents", []):
                                # Filter by agent type and capabilities
                                if agent_info.get("agent_type") == agent_type:
                                    if capabilities:
                                        agent_capabilities = agent_info.get("testing_capabilities", [])
                                        if not all(cap in agent_capabilities for cap in capabilities):
                                            continue
                                    
                                    # Create RemoteAgent instance
                                    remote_agent = RemoteAgent(
                                        name=agent_info["name"],
                                        endpoint=endpoint,
                                        agent_type=agent_info["agent_type"],
                                        capabilities=agent_info,
                                        protocol_version="1.0.0",
                                        last_seen=datetime.utcnow()
                                    )
                                    
                                    discovered_agents.append(remote_agent)
                                    self.known_agents[remote_agent.name] = remote_agent
                                    
            except Exception as e:
                logger.debug(f"Discovery failed for {endpoint}: {e}")
                continue
                
        logger.info(f"Discovered {len(discovered_agents)} accessibility agents")
        return discovered_agents
    
    async def send_request(
        self,
        target_agent: RemoteAgent,
        method_name: str,
        params: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Send JSON-RPC 2.0 request to a remote agent via A2A protocol
        
        Args:
            target_agent: Remote agent to communicate with
            method_name: Method to call (e.g., "analyze_accessibility")
            params: Method parameters
            timeout: Request timeout in seconds
            
        Returns:
            Response data from remote agent
        """
        request_id = str(uuid.uuid4())
        
        # JSON-RPC 2.0 request format
        request_data = {
            "jsonrpc": "2.0",
            "method": f"{target_agent.name}.{method_name}",
            "params": params,
            "id": request_id
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.post(
                    f"{target_agent.endpoint}/a2a/rpc",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        response_data = await response.json()
                        
                        # Check for JSON-RPC error
                        if "error" in response_data:
                            raise Exception(f"Remote agent error: {response_data['error']}")
                            
                        return response_data.get("result", {})
                    else:
                        raise Exception(f"HTTP error {response.status}: {await response.text()}")
                        
        except asyncio.TimeoutError:
            raise Exception(f"Request timeout after {timeout} seconds")
        except Exception as e:
            logger.error(f"A2A request failed to {target_agent.name}: {e}")
            raise
    
    async def coordinate_accessibility_test(
        self,
        remote_agent: RemoteAgent,
        url: str,
        test_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Coordinate accessibility testing with a remote agent
        
        Args:
            remote_agent: Remote agent to coordinate with
            url: Target URL for accessibility testing
            test_options: Optional testing configuration
            
        Returns:
            Accessibility test results from remote agent
        """
        test_options = test_options or {}
        
        params = {
            "url": url,
            "wcag_level": test_options.get("wcag_level", "AA"),
            "test_types": test_options.get("test_types", ["comprehensive"])
        }
        
        try:
            result = await self.send_request(
                target_agent=remote_agent,
                method_name="analyze_accessibility", 
                params=params
            )
            
            # Update last seen timestamp
            remote_agent.last_seen = datetime.utcnow()
            
            return result
            
        except Exception as e:
            logger.error(f"Accessibility test coordination failed with {remote_agent.name}: {e}")
            raise
    
    async def get_agent_capabilities(self, remote_agent: RemoteAgent) -> Dict[str, Any]:
        """
        Get capabilities from a remote agent
        
        Args:
            remote_agent: Remote agent to query
            
        Returns:
            Agent capabilities and supported features
        """
        try:
            result = await self.send_request(
                target_agent=remote_agent,
                method_name="get_capabilities",
                params={}
            )
            
            # Update agent capabilities cache
            remote_agent.capabilities.update(result)
            remote_agent.last_seen = datetime.utcnow()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get capabilities from {remote_agent.name}: {e}")
            return {}
    
    async def ping_agent(self, remote_agent: RemoteAgent) -> bool:
        """
        Ping a remote agent to check availability
        
        Args:
            remote_agent: Remote agent to ping
            
        Returns:
            True if agent is available, False otherwise
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{remote_agent.endpoint}/a2a/health") as response:
                    if response.status == 200:
                        remote_agent.last_seen = datetime.utcnow()
                        return True
                    
        except Exception as e:
            logger.debug(f"Ping failed for {remote_agent.name}: {e}")
            
        return False
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """
        Broadcast message to all active WebSocket connections
        
        Args:
            message: Message to broadcast
        """
        if self.is_server_running:
            await self.local_server.broadcast_to_connections(message)
    
    def get_agent_registry(self) -> Dict[str, RemoteAgent]:
        """Get all known agents in the registry"""
        return self.known_agents.copy()
    
    def get_available_agents(self) -> List[RemoteAgent]:
        """Get list of agents that were recently seen (last 5 minutes)"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        return [
            agent for agent in self.known_agents.values()
            if agent.last_seen and agent.last_seen > cutoff_time
        ]
# A2A Protocol utilities
class A2AMessageHandler(ABC):
    """Abstract base class for handling A2A messages"""
    
    @abstractmethod
    async def handle_request(self, request: A2ARequest) -> A2AResponse:
        """Handle incoming A2A request"""
        pass
    
    @abstractmethod
    async def handle_broadcast(self, message: str, data: Dict[str, Any]) -> bool:
        """Handle broadcast message"""
        pass


class AccessibilityA2AHandler(A2AMessageHandler):
    """A2A message handler for accessibility testing agents"""
    
    def __init__(self, local_agent):
        self.local_agent = local_agent
    
    async def handle_request(self, request: A2ARequest) -> A2AResponse:
        """Handle accessibility testing request from remote agent"""
        try:
            if request.action == "analyze_accessibility":
                url = request.payload.get('url')
                context = request.payload
                
                # Execute local analysis
                issues = await self.local_agent.analyze(url, context)
                
                return A2AResponse(
                    request_id=request.request_id,
                    success=True,
                    data={
                        'agent_name': self.local_agent.name,
                        'issues': [
                            {
                                'issue_type': issue.issue_type,
                                'severity': issue.severity.value,
                                'description': issue.description,
                                'element_selector': issue.element_selector,
                                'wcag_guideline': issue.wcag_guideline,
                                'suggested_fix': issue.suggested_fix,
                                'evidence': issue.evidence
                            }
                            for issue in issues
                        ]
                    },
                    timestamp=datetime.now()
                )
            
            elif request.action == "get_capabilities":
                capabilities = await self.local_agent.get_capabilities()
                return A2AResponse(
                    request_id=request.request_id,
                    success=True,
                    data=capabilities,
                    timestamp=datetime.now()
                )
            
            else:
                return A2AResponse(
                    request_id=request.request_id,
                    success=False,
                    error=f"Unknown action: {request.action}",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            return A2AResponse(
                request_id=request.request_id,
                success=False,
                error=str(e),
                timestamp=datetime.now()
            )
    
    async def handle_broadcast(self, message: str, data: Dict[str, Any]) -> bool:
        """Handle broadcast message"""
        try:
            if message == "agent_discovery":
                # Respond to agent discovery broadcasts
                print(f"Agent discovery broadcast received by {self.local_agent.name}")
                return True
            
            elif message == "system_shutdown":
                # Handle system shutdown notifications
                print(f"System shutdown notification received by {self.local_agent.name}")
                return True
            
            return True
            
        except Exception as e:
            print(f"Broadcast handling failed: {e}")
            return False
