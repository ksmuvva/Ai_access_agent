"""
A2A HTTP Server Implementation
JSON-RPC 2.0 based HTTP server for agent-to-agent communication
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from aiohttp import web, WSMsgType
from aiohttp.web import Application, Request, Response, WebSocketResponse
import aiohttp_cors
from dataclasses import asdict

from .agent_card import AccessibilityAgentCard, A2AMethod
from .base_agent import BaseAccessibilityAgent

logger = logging.getLogger(__name__)


class A2AServer:
    """
    A2A Protocol HTTP Server
    Implements JSON-RPC 2.0 over HTTP with WebSocket support for real-time communication
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app: Optional[Application] = None
        self.agents: Dict[str, BaseAccessibilityAgent] = {}
        self.agent_cards: Dict[str, AccessibilityAgentCard] = {}
        self.method_handlers: Dict[str, Callable] = {}
        self.active_connections: List[WebSocketResponse] = []
        
    def register_agent(self, agent: BaseAccessibilityAgent, agent_card: AccessibilityAgentCard):
        """
        Register an accessibility agent with the A2A server
        
        Args:
            agent: The agent instance to register
            agent_card: Agent card defining capabilities and methods
        """
        # Validate agent card
        validation_errors = agent_card.validate()
        if validation_errors:
            raise ValueError(f"Invalid agent card: {validation_errors}")
            
        self.agents[agent_card.name] = agent
        self.agent_cards[agent_card.name] = agent_card
        
        # Register method handlers
        for method in agent_card.methods:
            method_key = f"{agent_card.name}.{method.name}"
            self.method_handlers[method_key] = self._create_method_handler(agent, method)
            
        logger.info(f"Registered agent: {agent_card.name} with {len(agent_card.methods)} methods")
    
    def _create_method_handler(self, agent: BaseAccessibilityAgent, method: A2AMethod) -> Callable:
        """Create a method handler for an agent method"""
        async def handler(params: Dict[str, Any]) -> Dict[str, Any]:
            try:
                # Route to appropriate agent method
                if method.name == "analyze_accessibility":
                    from google.adk.agents.invocation_context import InvocationContext
                    context = InvocationContext.create_new()
                    url = params.get("url")
                    issues = await agent.analyze_accessibility(url, context)
                    
                    return {
                        "issues": [asdict(issue) for issue in issues],
                        "summary": {
                            "total_issues": len(issues),
                            "url": url,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        "compliance_score": self._calculate_compliance_score(issues)
                    }
                    
                elif method.name == "get_capabilities":
                    return {
                        "wcag_version": "2.2",
                        "compliance_levels": ["A", "AA", "AAA"],
                        "testing_capabilities": agent.get_capabilities(),
                        "supported_browsers": ["chromium", "firefox", "webkit"]
                    }
                    
                else:
                    # Generic method handler - delegate to agent
                    if hasattr(agent, method.name):
                        method_func = getattr(agent, method.name)
                        if asyncio.iscoroutinefunction(method_func):
                            return await method_func(**params)
                        else:
                            return method_func(**params)
                    else:
                        raise NotImplementedError(f"Method {method.name} not implemented")
                        
            except Exception as e:
                logger.error(f"Error executing method {method.name}: {e}")
                raise
                
        return handler
    
    def _calculate_compliance_score(self, issues: List) -> float:
        """Calculate compliance score based on issues found"""
        if not issues:
            return 100.0
            
        # Simple scoring algorithm - can be enhanced
        total_weight = len(issues)
        penalty_weight = sum([
            3 if issue.severity.value == "critical" else
            2 if issue.severity.value == "high" else
            1 if issue.severity.value == "medium" else
            0.5 for issue in issues
        ])
        
        score = max(0, 100 - (penalty_weight / total_weight * 20))
        return round(score, 2)
    
    async def setup_app(self) -> Application:
        """Setup aiohttp application with A2A endpoints"""
        app = web.Application()
        
        # Enable CORS for cross-origin requests
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # A2A Protocol endpoints
        app.router.add_post('/a2a/rpc', self.handle_jsonrpc)
        app.router.add_get('/a2a/agents', self.list_agents)
        app.router.add_get('/a2a/agents/{agent_name}', self.get_agent_card)
        app.router.add_get('/a2a/health', self.health_check)
        app.router.add_get('/a2a/ws', self.websocket_handler)
        
        # Add CORS to all routes
        for route in list(app.router.routes()):
            cors.add(route)
            
        self.app = app
        return app
    
    async def handle_jsonrpc(self, request: Request) -> Response:
        """
        Handle JSON-RPC 2.0 requests for A2A protocol
        
        JSON-RPC 2.0 Request Format:
        {
            "jsonrpc": "2.0",
            "method": "agent_name.method_name", 
            "params": {...},
            "id": "request_id"
        }
        """
        try:
            data = await request.json()
            
            # Validate JSON-RPC 2.0 format
            if data.get("jsonrpc") != "2.0":
                return self._jsonrpc_error(-32600, "Invalid Request", data.get("id"))
                
            method = data.get("method")
            params = data.get("params", {})
            request_id = data.get("id")
            
            if not method:
                return self._jsonrpc_error(-32600, "Invalid Request: method required", request_id)
            
            # Execute method
            if method in self.method_handlers:
                try:
                    result = await self.method_handlers[method](params)
                    
                    response_data = {
                        "jsonrpc": "2.0",
                        "result": result,
                        "id": request_id
                    }
                    
                    return web.json_response(response_data)
                    
                except Exception as e:
                    logger.error(f"Method execution error: {e}")
                    return self._jsonrpc_error(-32603, f"Internal error: {str(e)}", request_id)
            else:
                return self._jsonrpc_error(-32601, f"Method not found: {method}", request_id)
                
        except json.JSONDecodeError:
            return self._jsonrpc_error(-32700, "Parse error", None)
        except Exception as e:
            logger.error(f"JSON-RPC handler error: {e}")
            return self._jsonrpc_error(-32603, "Internal error", None)
    
    def _jsonrpc_error(self, code: int, message: str, request_id: Any) -> Response:
        """Create JSON-RPC 2.0 error response"""
        error_data = {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            },
            "id": request_id
        }
        return web.json_response(error_data, status=400)
    
    async def list_agents(self, request: Request) -> Response:
        """List all registered agents and their capabilities"""
        agents_info = []
        
        for name, card in self.agent_cards.items():
            agents_info.append({
                "name": card.name,
                "description": card.description,
                "version": card.version,
                "agent_type": card.agent_type,
                "wcag_version": card.wcag_version,
                "compliance_levels": card.compliance_levels,
                "testing_capabilities": card.testing_capabilities,
                "methods": [method.name for method in card.methods],
                "endpoint": f"/a2a/agents/{name}"
            })
            
        return web.json_response({
            "agents": agents_info,
            "total": len(agents_info),
            "protocol_version": "1.0.0"
        })
    
    async def get_agent_card(self, request: Request) -> Response:
        """Get detailed agent card for specific agent"""
        agent_name = request.match_info['agent_name']
        
        if agent_name not in self.agent_cards:
            return web.json_response(
                {"error": f"Agent not found: {agent_name}"},
                status=404
            )
            
        card = self.agent_cards[agent_name]
        return web.json_response(json.loads(card.to_json()))
    
    async def health_check(self, request: Request) -> Response:
        """A2A server health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "agents_registered": len(self.agents),
            "active_connections": len(self.active_connections),
            "protocol_version": "1.0.0"
        })
    
    async def websocket_handler(self, request: Request) -> WebSocketResponse:
        """WebSocket handler for real-time A2A communication"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.active_connections.append(ws)
        logger.info(f"WebSocket connection established. Total: {len(self.active_connections)}")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        
                        # Handle WebSocket JSON-RPC requests
                        if data.get("jsonrpc") == "2.0":
                            method = data.get("method")
                            params = data.get("params", {})
                            
                            if method in self.method_handlers:
                                result = await self.method_handlers[method](params)
                                response = {
                                    "jsonrpc": "2.0",
                                    "result": result,
                                    "id": data.get("id")
                                }
                                await ws.send_str(json.dumps(response))
                            else:
                                error_response = {
                                    "jsonrpc": "2.0",
                                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                                    "id": data.get("id")
                                }
                                await ws.send_str(json.dumps(error_response))
                                
                    except json.JSONDecodeError:
                        error_response = {
                            "jsonrpc": "2.0", 
                            "error": {"code": -32700, "message": "Parse error"},
                            "id": None
                        }
                        await ws.send_str(json.dumps(error_response))
                        
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            if ws in self.active_connections:
                self.active_connections.remove(ws)
            logger.info(f"WebSocket connection closed. Total: {len(self.active_connections)}")
            
        return ws
    
    async def broadcast_to_connections(self, message: Dict[str, Any]):
        """Broadcast message to all active WebSocket connections"""
        if not self.active_connections:
            return
            
        message_str = json.dumps(message)
        
        # Remove closed connections
        active_connections = []
        for ws in self.active_connections:
            if not ws.closed:
                try:
                    await ws.send_str(message_str)
                    active_connections.append(ws)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {e}")
                    
        self.active_connections = active_connections
    
    async def start(self):
        """Start the A2A HTTP server"""
        if not self.app:
            await self.setup_app()
            
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"A2A Server started on {self.host}:{self.port}")
        logger.info(f"Registered agents: {list(self.agents.keys())}")
        logger.info(f"Available endpoints:")
        logger.info(f"  - POST /a2a/rpc (JSON-RPC 2.0)")
        logger.info(f"  - GET /a2a/agents (List agents)")
        logger.info(f"  - GET /a2a/agents/{{name}} (Agent card)")
        logger.info(f"  - GET /a2a/health (Health check)")
        logger.info(f"  - GET /a2a/ws (WebSocket)")
    
    async def stop(self):
        """Stop the A2A HTTP server"""
        if self.app:
            await self.app.cleanup()
            logger.info("A2A Server stopped")
