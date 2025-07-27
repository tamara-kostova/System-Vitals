import asyncio
import json
import logging
import sys
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPClient:
    """MCP Client to communicate with system info server"""

    def __init__(self):
        self.process = None
        self.available_tools = []
        self.is_connected = False

    async def start(self):
        """Start MCP server process"""
        try:
            self.process = await asyncio.create_subprocess_exec(
                sys.executable,
                "src/server.py",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            logger.info("MCP Server started")
            await self._initialize()
            await self._load_tools()
            self.is_connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            self.is_connected = False
            return False

    async def _send_message(self, message: Dict) -> Dict:
        """Send message to MCP server"""
        if not self.process:
            raise Exception("MCP server not started")

        try:
            message_str = json.dumps(message) + "\n"
            self.process.stdin.write(message_str.encode())
            await self.process.stdin.drain()

            response_line = await asyncio.wait_for(
                self.process.stdout.readline(), timeout=10
            )

            response = json.loads(response_line.decode().strip())
            return response

        except Exception as e:
            logger.error(f"MCP communication error: {e}")
            raise Exception(f"MCP communication failed: {e}")

    async def _initialize(self):
        """Initialize MCP connection"""
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "fastapi-mcp-client", "version": "1.0.0"},
            },
        }

        response = await self._send_message(init_message)
        if "result" not in response:
            raise Exception("MCP initialization failed")
        logger.info("MCP connection initialized")

    async def _load_tools(self):
        """Load available tools"""
        list_message = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

        response = await self._send_message(list_message)
        if "result" in response:
            self.available_tools = response["result"]["tools"]
            logger.info(f"Loaded {len(self.available_tools)} MCP tools")
        else:
            logger.error("Failed to load MCP tools")

    async def get_system_info(self) -> Dict:
        """Get system information from MCP server"""
        call_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_system_info", "arguments": {}},
        }

        response = await self._send_message(call_message)
        if "result" in response:
            system_data = json.loads(response["result"]["content"][0]["text"])
            return system_data
        else:
            raise Exception(
                f"Failed to get system info: {response.get('error', 'Unknown error')}"
            )

    async def call_tool(self, tool_name: str, arguments: Dict = None) -> str:
        """Call an MCP tool and return the result"""
        if arguments is None:
            arguments = {}

        call_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        response = await self._send_message(call_message)
        if "result" in response:
            content = response["result"]["content"][0]["text"]
            return content
        else:
            return f"Error calling tool {tool_name}: {response.get('error', 'Unknown error')}"

    def get_tools_for_groq(self) -> List[Dict]:
        """Convert MCP tools to Groq function calling format"""
        groq_tools = []
        for tool in self.available_tools:
            groq_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool.get(
                        "inputSchema",
                        {"type": "object", "properties": {}, "required": []},
                    ),
                },
            }
            groq_tools.append(groq_tool)
        return groq_tools

    async def close(self):
        """Close MCP server"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.is_connected = False
